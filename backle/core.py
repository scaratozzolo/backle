import pandas as pd
from backle.data_factory import BaseDataFactory

class Backle:

    def __init__(self, allocation_matrix: pd.DataFrame, data_source: BaseDataFactory):

        assert isinstance(allocation_matrix, pd.DataFrame), "allocation_matrix is not of type pandas.DataFrame"
        assert isinstance(allocation_matrix.index, pd.DatetimeIndex), "allocation_matrix index is not of type pandas.DatetimeIndex"
        self.allocation_matrix = allocation_matrix

        assert isinstance(data_source, BaseDataFactory), "data_source is not of type backle.data_factory.BaseDataFactory"
        self.data_source = data_source



if __name__ == "__main__":

    pass