from controllers.alphavantage import Alphavantage
from controllers.robinhood import Robinhood
from os import environ as env 
from dotenv import load_dotenv
load_dotenv()

Alpha = Alphavantage(env['ALPHAVANTAGE_API'])
RH_Bot = Robinhood(env['RH_UNAME'], env['RH_PASSWORD'])
Alpha.get_daily_ts()


