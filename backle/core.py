import datetime
from typing import Optional, List, Union
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
import pandas_market_calendars as mcal
import numpy as np
import pytz
from loguru import logger
from tqdm import tqdm
from backle.data_factory import BaseDataFactory
from backle.environment import BaseEnvironment

class Backle:

    def __init__(self, allocation_matrix: pd.DataFrame, data_source: BaseDataFactory):

        assert isinstance(allocation_matrix, pd.DataFrame), "allocation_matrix is not of type pandas.DataFrame"
        assert isinstance(allocation_matrix.index, pd.DatetimeIndex), "allocation_matrix index is not of type pandas.DatetimeIndex"
        self.allocation_matrix = allocation_matrix

        assert isinstance(data_source, BaseDataFactory), "data_source is not of type backle.data_factory.BaseDataFactory"
        self.data_source = data_source

    def run(self, backtest_env: BaseEnvironment = BaseEnvironment):

        # test to make sure backtest_env is a BaseEnvironment Class
        assert issubclass(backtest_env, BaseEnvironment), "backtest_env is not a subclass of backle.environment.BaseEnvironment"

        if backtest_env.TRADE_AT not in ['open', 'close']:
            raise ValueError("trade_at should be one of the following: ['open', 'close']")

        # make sure STARTING_PORTFOLIO_VALUE is at least $1
        if backtest_env.STARTING_PORTFOLIO_VALUE < 1:
            raise ValueError("STARTING_PORTFOLIO_VALUE must be greater than or equal to 1")

        if self.data_source.price_data is None:
            if self.data_source.symbols is None:
                symbols = self.allocation_matrix.columns
            else:
                symbols = self.data_source.symbols
            self.data_source.pull_price_data(symbols=symbols, start=backtest_env.START_DATE, end=backtest_env.END_DATE)
        else:
            # make sure the columns of the allocation matrix and price data are same length
            # TODO make sure the columns are equal (i.e the order of the columns and the names are the same)
            assert self.allocation_matrix.shape[1] == self.data_source.price_data.shape[1], f"allocation_matrix and DataFactory.price_data don't have the same number of columns ({self.allocation_matrix.shape[1]} != {self.data_source.price_data.shape[1]})"

        # set starting values
        current_portfolio_value = backtest_env.STARTING_PORTFOLIO_VALUE
        current_portfolio_holdings = {i: [] for i in self.allocation_matrix.columns}

        self.portfolio_history = pd.DataFrame({'date':[], 'portfolio_value': [], 'cash': [], **current_portfolio_holdings})
        self.position_history = pd.DataFrame({'date':[], 'cash': [], **current_portfolio_holdings}) # similar to portfolio_history but values are in dollars https://github.com/stefan-jansen/pyfolio-reloaded/blob/main/src/pyfolio/tears.py#L109
        self.transaction_history = pd.DataFrame({'date':[], 'amount':[], 'price':[], 'symbol':[]})
    
        shares = pd.Series([0.0]*len(self.allocation_matrix.columns), index=self.allocation_matrix.columns)
        cash = current_portfolio_value
        cost_basis = 0

        # make a copy of allocation matrix between the start and end dates
        _allocation_matrix = self.allocation_matrix.copy().loc[backtest_env.START_DATE:backtest_env.END_DATE]
        if backtest_env.REINDEX_ALLOCATION_MATRIX:
            # if REINDEX_ALLOCATION_MATRIX is true, we will create a new index that contains every date minus holidays between the start and end dates to compute portfolio value
            nyse = mcal.get_calendar('NYSE')
            early = nyse.schedule(start_date=backtest_env.START_DATE, end_date=backtest_env.END_DATE if backtest_env.END_DATE is not None else self.data_source.price_data.index[-1], tz=pytz.timezone('America/New_York'))
            idx = mcal.date_range(early, frequency=backtest_env.REINDEX_DATE_FREQ).normalize()
            _allocation_matrix = _allocation_matrix.reindex(idx)


        for i, row in tqdm(_allocation_matrix.iterrows(), total=len(_allocation_matrix)):
            # loop over every row of the allocation matrix
            try:
                # get price data for current timestamp
                price_row = self.data_source.price_data.loc[i]
            except KeyError as excp:
                # KeyError if price data doesn't exist
                if not self._is_business_day(i):
                    logger.warning(f"Price data missing for {i}, skipping...")
                else:
                    logger.error(excp)
                continue
                
            # the current cash value of each asset
            cur_share_value_ind = shares * price_row
            # current portfolio value is cash + sum of individual values
            current_portfolio_value = cash + cur_share_value_ind.sum()
            # if the allocation row contains any values (not all null) we will rebalance
            # TODO need to include transaction costs here
            if not row.isnull().all():
                # make copy of old shares
                shares_old = shares
                # new shares is equal to the current portfolio value * allocation percentage to get max cash allowed into each asset
                # divided by current share price to get number of shares
                shares = (current_portfolio_value * row) / price_row
                if not backtest_env.FRACTIONAL_SHARES:
                    # if FRACTIONAL_SHARES are not allowed, we round down
                    shares = np.floor(shares)

                # get the difference between the new shares and old shares to determine how much to buy or sell
                shares_diff = shares - shares_old

                # cash cost of each asset
                cost_basis_ind = shares * price_row
                # total cost
                cost_basis = cost_basis_ind.sum()
                # new cash amount is the current portfolio value minus the total cost
                cash = current_portfolio_value - cost_basis

                # add buy/sell amounts into transactions
                for amount, (symbol, price) in zip(shares_diff, price_row.items()):
                    self.transaction_history.loc[len(self.transaction_history.index)] = [i, amount, price, symbol]

            # store portfolio info for this timestamp
            self.portfolio_history.loc[len(self.portfolio_history.index)] = [i, current_portfolio_value, cash] + shares.tolist()
            self.position_history.loc[len(self.position_history.index)] = [i, cash] + cur_share_value_ind.tolist()


        # set index to date
        self.portfolio_history.set_index("date", inplace=True)
        self.position_history.set_index("date", inplace=True)
        self.transaction_history.set_index("date", inplace=True)
    
    @staticmethod
    def _is_business_day(date):
        return bool(len(pd.bdate_range(date, date)))

    def pyfolio_tear_sheet(self, **kwargs):

        import pyfolio as pf

        assert hasattr(self, 'portfolio_history'), "You must run the backtest before getting the tear sheet"

        # calculate percent return
        returns = self.portfolio_history['portfolio_value'].pct_change()
        # remove time zone info
        returns.index = returns.index.tz_convert(None) # possible issue without this if there are short assets

        pf.create_full_tear_sheet(returns, positions=self.position_history, transactions=self.transaction_history, **kwargs)

    def quantstats_tear_sheet(self, html_report=False, **kwargs):

        import quantstats as qs

        assert hasattr(self, 'portfolio_history'), "You must run the backtest before getting the tear sheet"

        # calculate percent return
        returns = self.portfolio_history['portfolio_value'].pct_change()
        # remove time zone info
        returns.index = returns.index.tz_convert(None) # https://github.com/ranaroussi/quantstats/issues/245

        if html_report:
            qs.reports.html(returns, output="report.html", **kwargs) # need to specify output file but it doesn't apply
        else:
            qs.reports.full(returns, **kwargs)


if __name__ == "__main__":

    pass