import numpy as np
import math
inputs = [[1, 2 , 3, 2.5], [2.0, 5.0, -1.0, 2.0], [-1.5, 2.7, 3.3, -0.8]]
E = math.e
output = []


class Layer_Dense:
    def __init__(self, n_inputs, n_neurons):
        self.weights = 0.10 * np.random.rand(n_inputs, n_neurons)
        self.biases = np.zeros((1, n_neurons))
        print (self.weights)

    def forward(self, inputs):
        self.output = np.dot(inputs, self.weights) + self.biases    

class Activation_ReLU:
    def forward(self, inputs):
        self.output = np.maximum(0, inputs)

class Activation_Softmax:
    def forward(self, inputs):
        exp_values = np.exp(inputs - np.max(inputs, axis = 1, keepdims = True))
        self.output = exp_values / np.sum(exp_values, axis = 1, keepdims = True)

layer1 = Layer_Dense(4, 5)
layer1.forward(inputs)
activation1 = Activation_ReLU()
activation1.forward(layer1.output)
layer2 = Layer_Dense(5, 3)
layer2.forward(activation1.output)
activation2 = Activation_Softmax()
activation2.forward(layer2.output)
print (activation2.output)