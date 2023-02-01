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

        assert issubclass(backtest_env, BaseEnvironment), "backtest_env is not a subclass of backle.environment.BaseEnvironment"

        if backtest_env.TRADE_AT not in ['open', 'close']:
            raise ValueError("trade_at should be one of the following: ['open', 'close']")

        if backtest_env.STARTING_PORTFOLIO_VALUE < 1:
            raise ValueError("STARTING_PORTFOLIO_VALUE must be greater than or equal to 1")

        if self.data_source.price_data is None:
            if self.data_source.symbols is None:
                symbols = self.allocation_matrix.columns
            else:
                symbols = self.data_source.symbols
            self.data_source.pull_price_data(symbols=symbols, start=backtest_env.START_DATE, end=backtest_env.END_DATE)
        else:
            assert self.allocation_matrix.shape[1] == self.data_source.price_data.shape[1], f"allocation_matrix and DataFactory.price_data don't have the same number of columns ({self.allocation_matrix.shape[1]} != {self.data_source.price_data.shape[1]})"

        current_portfolio_value = backtest_env.STARTING_PORTFOLIO_VALUE
        current_portfolio_holdings = {i: [] for i in self.allocation_matrix.columns}

        self.portfolio_history = pd.DataFrame({'Date':[], 'Portfolio_Value': [], 'Cash': [], **current_portfolio_holdings})

        # TODO allocation matrix can potentially only have rebalance time stamps, but should be able to calc portfolio inbetween rebalancing which means taking the index from the prices
    
        shares = pd.Series([0.0]*len(self.allocation_matrix.columns), index=self.allocation_matrix.columns)
        cash = current_portfolio_value
        cost_basis = 0

        _allocation_matrix = self.allocation_matrix.copy().loc[backtest_env.START_DATE:backtest_env.END_DATE]
        if backtest_env.REINDEX_ALLOCATION_MATRIX:
            nyse = mcal.get_calendar('NYSE')
            early = nyse.schedule(start_date=backtest_env.START_DATE, end_date=backtest_env.END_DATE if backtest_env.END_DATE is not None else self.allocation_matrix.index[-1], tz=pytz.timezone('America/New_York'))
            idx = mcal.date_range(early, frequency=backtest_env.REINDEX_DATE_FREQ).normalize()
            _allocation_matrix = _allocation_matrix.reindex(idx)


        for i, row in tqdm(_allocation_matrix.iterrows(), total=len(_allocation_matrix)):

            try:
                price_row = self.data_source.price_data.loc[i]
            except KeyError as excp:
                if not self._is_business_day(i):
                    logger.warning(f"Price data missing for {i}, skipping...")
                else:
                    logger.error(excp)
                continue
                

            cur_share_value = shares @ price_row

            current_portfolio_value = cash + cur_share_value
            # need to include transaction costs here
            if not row.isnull().all():
                shares = (current_portfolio_value * row) / price_row
            if not backtest_env.FRACTIONAL_SHARES:
                shares = np.floor(shares)

            cost_basis = shares @ price_row
            cash = current_portfolio_value - cost_basis
            

            self.portfolio_history.loc[len(self.portfolio_history.index)] = [i, current_portfolio_value, cash] + shares.tolist()


        self.portfolio_history.set_index("Date", inplace=True)
    
    @staticmethod
    def _is_business_day(date):
        return bool(len(pd.bdate_range(date, date)))

    def pyfolio_tear_sheet(self, **kwargs):

        try:
            import pyfolio as pf
        except ImportError:
            logger.error("pyfolio not installed: please run 'pip install pyfolio-reloaded'")

        assert hasattr(self, 'portfolio_history'), "You must run the backtest before getting the tear sheet"

        returns = self.portfolio_history['Portfolio_Value'].pct_change()

        pf.create_returns_tear_sheet(returns, **kwargs)

    def quantstats_tear_sheet(self, html_report=False, **kwargs):

        try:
            import quantstats as qs
        except ImportError:
            logger.error("quantstats not installed: please run 'pip install quantstats'")

        assert hasattr(self, 'portfolio_history'), "You must run the backtest before getting the tear sheet"

        returns = self.portfolio_history['Portfolio_Value'].pct_change()
        returns.index = returns.index.tz_convert(None) # https://github.com/ranaroussi/quantstats/issues/245

        if html_report:
            qs.reports.html(returns, output="report.html", **kwargs) # need to specify output file but it doesn't apply
        else:
            qs.reports.full(returns, **kwargs)


if __name__ == "__main__":

    pass