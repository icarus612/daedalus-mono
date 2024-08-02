import tensorflow as tf
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Flatten, Dense
import os

from abstract_base_classes.ann_shell import ANN_Shell

class Digit_Recognition_MLP(ANN_Shell):
	def __init__(self):
		self.model = load_model(l) if os.path.isfile(l) else self.build() 

	def build(self, imageSize=[28, 28], layers=2):
		model = Sequential([
			Flatten(input_shape=(imageSize[0], imageSize[1])),
			*[Dense(128, activation='relu') for _ in range(layers)],
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

		
if __name__ == "__main__":
	mlp = Digit_Recognition_MLP()
	mlp.train()
	mlp.save()