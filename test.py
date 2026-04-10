import numpy as np

a = np.random.random((10, 30))
b = np.zeros((2, 12))
print(a)
print(np.average(a, axis=1).shape)
