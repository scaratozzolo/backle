import datetime
from typing import Optional, List, Union
import pandas as pd
import numpy as np
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

    def run(self, backtest_env: BaseEnvironment = BaseEnvironment()):

        assert isinstance(backtest_env, BaseEnvironment), "backtest_env is not of type backle.environment.BaseEnvironment"

        if backtest_env.TRADE_AT not in ['open', 'close']:
            raise ValueError("trade_at should be one of the following: ['open', 'close']")

        if self.data_source.price_data is None:
            if self.data_source.symbols is None:
                symbols = self.allocation_matrix.columns
            else:
                symbols = self.data_source.symbols
            self.data_source.pull_price_data(symbols=symbols, start=backtest_env.START_DATE, end=backtest_env.END_DATE)
        else:
            assert self.allocation_matrix.shape[1] == self.data_source.price_data.shape[1], f"allocation_matrix and DataFactory.price_data don't have the same number of columns ({self.allocation_matrix.shape[1]} != {self.data_source.price_data.shape[1]})"

        portfolio_value = backtest_env.STARTING_PORTFOLIO_VALUE
        self.portfolio_history = pd.DataFrame({'Date':[], 'Portfolio_Value': []})

        if backtest_env.STARTING_PORTFOLIO_VALUE:
            # portfolio has a starting amount
            for i, row in tqdm(self.allocation_matrix.iterrows(), total=len(self.allocation_matrix)):
                price_row = self.data_source.price_data.loc[i]
        
        else:
            # portfolio is $0
            for i, row in tqdm(self.allocation_matrix.iterrows(), total=len(self.allocation_matrix)):
                price_row = self.data_source.price_data.loc[i]

                cur_value = row @ price_row # compute dot product

                self.portfolio_history.loc[len(self.portfolio_history.index)] = [i, cur_value]

        self.portfolio_history.set_index("Date", inplace=True)



if __name__ == "__main__":

    pass