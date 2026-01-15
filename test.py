import numpy as np

a = np.array([])
max_size = 3
for i in range(5):
    a = np.append(a, i)
    if a.size > max_size:
        a = a[-max_size:]
    print(a)

print(a)