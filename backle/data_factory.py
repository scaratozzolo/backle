import sys
from typing import Optional, List, Union
import datetime
import pandas as pd

try:
    import yfinance as yf
    YF_INSTALLED = True
except ImportError as excp:
    YF_INSTALLED = False

class BaseDataFactory:
    """
    Base factory to be inherited by other higher level data factories
    """
    pass


class DataFrameDataFactory(BaseDataFactory):
    """
    Data Factory using a DataFrame
    """
    def __init__(self, ohlcv_data: pd.DataFrame):
        """
        Init DataFrameDF

        Args:
            ohlcv_data (pd.DataFrame): A pandas.DataFrame containing the pricing data required for the backtest
        """

        assert isinstance(ohlcv_data, pd.DataFrame), "ohlcv_data is not of type pandas.DataFrame"
        assert isinstance(ohlcv_data.index, pd.DatetimeIndex), "ohlcv_data index is not of type pandas.DatetimeIndex"
        self.ohlcv_data = ohlcv_data
        

class YahooDataFactory(BaseDataFactory):
    """
    Data Factory for Yahoo Finance data
    """
    def __init__(self, symbols: Optional[list]=None):

        """
        Init YahooDF

        Args:
            data_column (str, optional): When to place trades. Defaults to 'Adj Close'.
            symbols (list, optional): List of symbols matching column names of the allocation matrix. Defaults to None.

        Raises:
            ImportError: To use the YahooDataFactory you must have yfinance installed.
        """

        if not YF_INSTALLED:
            raise ImportError("To use the YahooDataFactory you must have yfinance installed.")

        self.symbols = symbols

        self.ohlcv_data = None

    def pull_price_data(self, symbols: List[str], start: Union[str, datetime.datetime, datetime.date, None]=None, end: Union[str, datetime.datetime, datetime.date, None]=None):
        """
        Download pricing data from Yahoo Finance

        Args:
            symbols (_type_): list of symbols to send to Yahoo finance
            start (_type_, optional): Start date of data. Defaults to None.
            end (_type_, optional): End date of data. Defaults to None.
        """

        data = yf.download(symbols, start=start, end=end, progress=False)
        
        self.ohlcv_data = data


if __name__ == "__main__":

    import pandas as pd

    t = YahooDataFactory(symbols=["AAPL", "GOOG", "TSLA"])
    t.pull_price_data(t.symbols)
    print(t.ohlcv_data.columns.levels)
    # assert isinstance(t.ohlcv_data.index, pd.DataFrame), "No"
    # print(type(t))
    # assert isinstance(t, BaseDataFactory), "No"