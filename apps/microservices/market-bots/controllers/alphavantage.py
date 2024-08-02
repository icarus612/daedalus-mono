import requests
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt


class Alphavantage:
  def __init__(self, api_key, time_series='DAILY', output_size='full', interval=5, default_symbol="GOOG"):
    self.base_api = 'https://www.alphavantage.co/query'
    self.api_key = api_key
    self.time_series = time_series
    self.output_size = output_size
    self.interval = interval
    self.default_symbol = default_symbol
    
  def update_params(self, new_params):
    current_params = vars(self)
    for key in current_params.keys():
      if key in new_params.keys():
        current_params[key] = new_params[key] 
      
  def get_ticker_data(self, symbol=None):
    params = {
      "symbol": symbol or self.default_symbol,
      "function": f'TIME_SERIES_{self.time_series.upper()}',
      "interval": str(self.interval) + "min",
      "apikey": self.api_key,
      "outputsize": self.output_size
    }
    response = requests.get(self.base_api, params=params)
    if response.status_code == 200:
      return response.json()
    else:
      print("ERROR: ", response.status_code)
      
  def get_time_series(self, output_format='pandas'):
    return TimeSeries(key=self.api_key, output_format=output_format)
  
  def get_daily_ts(self, symbol=None):
    ts = self.get_time_series()
    s = symbol or self.default_symbol
    data = ts.get_daily(symbol=s, outputsize='compact')
    print(dir(ts))
    # Print the first few rows of data to see its structure
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['4. close'], label='Closing Price', color='blue')
    plt.title(f'{symbol} Stock Closing Prices')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()
    
