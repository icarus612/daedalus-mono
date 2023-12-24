import os
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM
import matplotlib.pyplot as plt

class Analyzer:
  def __init__(self, symbols=[], dir='models', name='market_analyzer.keras'):
		
    # Build dir and path for model
    cwd = os.path.join(os.getcwd(), dir)
    os.makedirs(cwd, exist_ok=True)
    l = os.path.join(cwd, name) # Combo of [cwd]/dir/name

    # Define class properties
    self.dir = dir
    self.name = name
    self.location = l 

    # load current modal or make new if none exsists. 
    self.model = load_model(l) if os.path.isfile(l) else self.build()     
    self.symbols = symbols
    
  def save(self):
    self.model.save(self.location)
    print("Model saved successfully.")

  def train(self, data, epochs=5, batch_size=32):
    (x_train, y_train), (x_test, y_test) = data
    x_train, x_test = x_train / 255.0, x_test / 255.0
    self.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

  def test(self):
    pass

  def build_new(self, input_layer, hidden_layers=2, hidden_neurons=128):
    model = Sequential()
    model.add(LSTM(50, activation='relu', input_shape=(input_layer.shape[1], input_layer.shape[2])))
    for i in range(hidden_layers):
      model.add(LSTM(hidden_neurons, activation='relu'))
    model.add(Dense(3))
    model.compile(optimizer='adam', loss='mean_squared_error')
    self.model = model
  
  def get_summary(self):
    return self.model.summary()