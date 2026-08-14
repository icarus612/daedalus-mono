from os import environ as env

from controllers.alphavantage import Alphavantage
from controllers.robinhood import Robinhood
from dotenv import load_dotenv

load_dotenv()

print("🤖 Market Bots Service Starting...")

try:
    Alpha = Alphavantage(env["ALPHAVANTAGE_API"])
    print("✅ Alpha Vantage controller initialized")
except Exception as e:
    print(f"❌ Alpha Vantage initialization failed: {e}")

try:
    RH_Bot = Robinhood(env["RH_UNAME"], env["RH_PASSWORD"])
    print("✅ Robinhood controller initialized")
except Exception as e:
    print(f"❌ Robinhood initialization failed: {e}")

# Only try to fetch data if we have a real API key (not demo)
if env.get("ALPHAVANTAGE_API") != "demo":
    try:
        Alpha.get_daily_ts()
        print("✅ Daily time series data fetched successfully")
    except Exception as e:
        print(f"❌ Failed to fetch time series data: {e}")
else:
    print("ℹ️  Demo API key detected. Replace with real API key to fetch data.")

print("🚀 Market Bots Service is running...")
