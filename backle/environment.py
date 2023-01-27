import datetime
from dateutil import tz


class BaseEnvironment:

    TRADE_AT = 'open'
    FRACTIONAL_SHARES = False
    START_DATE = datetime.datetime.now(tz=tz.gettz('America/New_York')) - datetime.timedelta(weeks=52)
    END_DATE = None
    COMMISSION_TYPE = "percentage"
    COMMISSION_AMOUNT = "0"
    STARTING_PORTFOLIO_VALUE = 0



if __name__ == '__main__':

    print(BaseEnvironment.TRADE_AT)