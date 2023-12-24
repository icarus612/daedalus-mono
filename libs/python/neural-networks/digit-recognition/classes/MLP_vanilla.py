import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split


class Digit_Recognition_MLP:
    def __init__(self, input_size, hidden_size, output_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        self.weights_input_hidden = np.random.randn(input_size, hidden_size)
        self.bias_hidden = np.zeros(hidden_size)
        self.weights_hidden_output = np.random.randn(hidden_size, output_size)
        self.bias_output = np.zeros(output_size)
        
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))
    
    def sigmoid_derivative(self, x):
        return x * (1 - x)
    
    def forward(self, X):
        self.hidden_input = np.dot(X, self.weights_input_hidden) + self.bias_hidden
        self.hidden_output = self.sigmoid(self.hidden_input)
        
        self.output_input = np.dot(self.hidden_output, self.weights_hidden_output) + self.bias_output
        self.output = self.sigmoid(self.output_input)
        
        return self.output
    
    def backward(self, X, y, output):
        error = y - output
        output_delta = error * self.sigmoid_derivative(output)
        
        hidden_error = np.dot(output_delta, self.weights_hidden_output.T)
        hidden_delta = hidden_error * self.sigmoid_derivative(self.hidden_output)
        
        self.weights_hidden_output += np.dot(self.hidden_output.T, output_delta)
        self.bias_output += np.sum(output_delta, axis=0)
        
        self.weights_input_hidden += np.dot(X.T, hidden_delta)
        self.bias_hidden += np.sum(hidden_delta, axis=0)
    
    def train(self, X, y, epochs, learning_rate):
        for epoch in range(epochs):
            output = self.forward(X)
            self.backward(X, y, output)
            
            if epoch % 10 == 0:
                loss = np.mean(np.square(y - output))
                print(f"Epoch {epoch}, Loss: {loss:.4f}")
    
    def predict(self, X):
        output = self.forward(X)
        predictions = np.argmax(output, axis=1)
        return predictions

if __name__ == "__main__":
    # Load MNIST dataset
    mnist = fetch_openml("mnist_784")
    X = mnist.data / 255.0  # Normalize pixel values
    y = mnist.target.astype(int)

    # Split dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define neural network parameters
    input_size = X_train.shape[1]
    hidden_size = 128
    output_size = 10
    epochs = 100
    learning_rate = 0.1

    # Create and train the neural network
    nn = Digit_Recognition_MLP(input_size, hidden_size, output_size)
    nn.train(X_train, np.eye(output_size)[y_train], epochs, learning_rate)

    # Evaluate the model on the test set
    predictions = nn.predict(X_test)
    accuracy = np.mean(predictions == y_test) * 100
    print(f"Test Accuracy: {accuracy:.2f}%")
