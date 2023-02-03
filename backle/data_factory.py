import sys
from typing import Optional, List, Union
import datetime
import pandas as pd
import yfinance as yf


class BaseDataFactory:
    """
    Base factory to be inherited by other higher level data factories
    """
    pass


class DataFrameDataFactory(BaseDataFactory):
    """
    Data Factory using a DataFrame
    """
    def __init__(self, price_data: pd.DataFrame):
        """
        Init DataFrameDF

        Args:
            price_data (pd.DataFrame): A pandas.DataFrame containing the pricing data required for the backtest
        """

        assert isinstance(price_data, pd.DataFrame), "price_data is not of type pandas.DataFrame"
        assert isinstance(price_data.index, pd.DatetimeIndex), "price_data index is not of type pandas.DatetimeIndex"
        self.price_data = price_data
        

class YahooDataFactory(BaseDataFactory):
    """
    Data Factory for Yahoo Finance data
    """
    def __init__(self, symbols: Optional[list]=None, price_to_use: str = "Adj Close", shift_data_n_periods: int = 0):

        """
        Init YahooDF

        Args:
            symbols (list, optional): List of symbols matching column names of the allocation matrix. If None, symbols will be used from the allocation_matrix column names. Defaults to None.

        Raises:
            ImportError: To use the YahooDataFactory you must have yfinance installed.
        """

        self.symbols = symbols

        if price_to_use not in ['Adj Close', 'Close', 'High', 'Low', 'Open']:
            raise ValueError("price_to_use should be one of the following: ['Adj Close', 'Close', 'High', 'Low', 'Open']")

        self.price_to_use = price_to_use
        self.shift_data_n_periods = shift_data_n_periods

        self.price_data = None

    def pull_price_data(self, symbols: List[str], start: Union[str, datetime.datetime, datetime.date, None]=None, end: Union[str, datetime.datetime, datetime.date, None]=None):
        """
        Download pricing data from Yahoo Finance

        Args:
            symbols (_type_): list of symbols to send to Yahoo finance
            start (_type_, optional): Start date of data. Defaults to None.
            end (_type_, optional): End date of data. Defaults to None.
        """

        data = yf.download(symbols, start=start, end=end, progress=False)
        
        self.price_data = data[self.price_to_use].shift(self.shift_data_n_periods)


if __name__ == "__main__":

    import pandas as pd

    t = YahooDataFactory(symbols=["AAPL", "GOOG", "TSLA"])
    t.pull_price_data(t.symbols)
    print(t.ohlcv_data.columns.levels)
    # assert isinstance(t.ohlcv_data.index, pd.DataFrame), "No"
    # print(type(t))
    # assert isinstance(t, BaseDataFactory), "No"