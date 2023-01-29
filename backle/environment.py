import datetime
import pytz


class BaseEnvironment:

    TRADE_AT = 'open'
    FRACTIONAL_SHARES = True
    START_DATE = pytz.timezone('America/New_York').localize(datetime.datetime(datetime.datetime.today().year-1, datetime.datetime.today().month, datetime.datetime.today().day))
    END_DATE = None
    COMMISSION_TYPE = "percentage"
    COMMISSION_AMOUNT = 0.0
    STARTING_PORTFOLIO_VALUE = 1



if __name__ == '__main__':

    print(BaseEnvironment.TRADE_AT)