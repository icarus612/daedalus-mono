import time
import robin_stocks as rh

# Set your Robinhood credentials
username = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
rh.login(username, password)

# Set the stock symbol you want to trade
stock_symbol = "AAPL"

# Define the trading interval in seconds (5 minutes)
trading_interval = 300

def buy_stock(symbol, quantity):
    try:
        rh.order_buy_market(symbol, quantity)
        print(f"Bought {quantity} shares of {symbol}")
    except rh.robinhood.RobinhoodError as e:
        print("Error:", e)

def sell_stock(symbol, quantity):
    try:
        rh.order_sell_market(symbol, quantity)
        print(f"Sold {quantity} shares of {symbol}")
    except rh.robinhood.RobinhoodError as e:
        print("Error:", e)

while True:
    # Buy or sell every 5 minutes
    buy_stock(stock_symbol, 1)  # You can adjust the quantity as needed
    time.sleep(trading_interval)
    
    sell_stock(stock_symbol, 1)  # You can adjust the quantity as needed
    time.sleep(trading_interval)
