import datetime
import pytz


class BaseEnvironment:
    """
    This is the parent class for creating trading environments.
    It implements all the possible variables for the simulation and initializes them with default values.
    """

    TRADE_AT = 'open' # trade at 'open' will use todays prices for the price_row, trade at 'close' will use tomorrows price_row
    FRACTIONAL_SHARES = True # if true, shares will be floats, if false shares will be ints
    START_DATE = pytz.timezone('America/New_York').localize(datetime.datetime(datetime.datetime.today().year-1, datetime.datetime.today().month, datetime.datetime.today().day)) # default start date of 1 year ago today, localized to American/New York timezone
    END_DATE = None # Default end date is None, typically meaning the end date is today
    REINDEX_ALLOCATION_MATRIX = True # allows for calculating portfolio values between dates in the allocation matrix, useful if the data is greater than daily
    REINDEX_DATE_FREQ = "1D" # https://pandas.pydata.org/docs/user_guide/timeseries.html#offset-aliases
    COMMISSION_TYPE = "percentage" # percentage, or dollar. determines if commission will be calulated as a portion of total cost or added as a flat value
    COMMISSION_AMOUNT = 0.0 # percentage amount or dollar amount
    STARTING_PORTFOLIO_VALUE = 1 # starting portfolio value in dollars



if __name__ == '__main__':

    print(BaseEnvironment.TRADE_AT)