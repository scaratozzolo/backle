import datetime


class BaseEnvironment:

    TRADE_AT = 'open'
    FRACTIONAL_SHARES = False
    START_DATE = datetime.date.today() - datetime.timedelta(weeks=52)
    END_DATE = None
    COMMISSION_TYPE = "percentage"
    COMMISSION_AMOUNT = "0"
    STARTING_PORTFOLIO_VALUE = 0