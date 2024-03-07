import numpy as np

import matplotlib.pyplot as plt

x_values = ['A', 'B', 'C', 'D', 'E']  # Replace the numbers with your desired strings
y_values = [1e4, 1e8, 1e2, 1e7, 1e6]

# Create a bar graph
plt.bar(x_values, y_values, width=0.6)

# Set the y-axis scale to log
plt.yscale('log')

# Set the y-axis limits (adjust as needed)
plt.ylim(1, 1e8)

# Display grid lines
#plt.grid(True)

# Set the y-axis ticks to display as 10, 10**2, 10**3, ..., 10**8
#plt.yticks([10**i for i in range(9)], [str(10**i) for i in range(9)])

# Show the plot
plt.show()
