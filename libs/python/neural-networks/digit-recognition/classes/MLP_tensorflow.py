import tensorflow as tf
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Flatten, Dense
import os


class Digit_Recognition_MLP:
	def __init__(self, name='MLP_TF.keras'):
		current_file = os.path.abspath(__file__)
		cd = os.path.dirname(current_file)
		models_dir = f'{cd}../models'
		os.makedirs(models_dir, exist_ok=True)
		location = os.path.join(models_dir, name) # Combo of [cwd]/dir/name
		
		# Define class properties
		self.name = name
		self.location = location
		
		# load current modal or make new if none exsists. 
		self.model = load_model(l) if os.path.isfile(l) else self.build() 

	def build(self, imageSize=[28, 28], layers=2):
		model = Sequential([
			# Flatten 28x28 images to a 1D array
			Flatten(input_shape=(imageSize[0], imageSize[1])),
			# Fully connected layer with 128 units and ReLU activation
			*[Dense(128, activation='relu') for _ in range(layers)],
			# Output layer with 10 units (one for each digit) and softmax activation
			Dense(10, activation='softmax')
		])
		return model

	def train(self, data=mnist.load_data(), epochs=5):
		# Load and preprocess data
		print("Starting Training")
		(x_train, y_train), (x_test, y_test) = data
		x_train, x_test = x_train / 255.0, x_test / 255.0


		# Compile the model
		self.model.compile(optimizer='adam',
												loss='sparse_categorical_crossentropy',
												metrics=['accuracy'])

		# Train the model
		self.model.fit(x_train, y_train, epochs=epochs,
										validation_data=(x_test, y_test))
		print("Training Complete!")

	def save(self):
		self.model.save(self.location)
		print("Model saved successfully.")
		
if __name__ == "__main__":
	mlp = Digit_Recognition_MLP()
	mlp.train()
	mlp.save()