import numpy as np
import pyqtgraph as pg
from PySide2.QtWidgets import QApplication, QMainWindow

x_values = [1, 2, 3, 4, 5]
y_values = [1e4, 1e8, 1e2, 1e7, 1e6]

# Create a bar graph
pg.setConfigOptions(antialias=True)
app = QApplication([])
win = QMainWindow()
plot = pg.PlotWidget()
win.setCentralWidget(plot)
plot.setLabel('left', 'Value')
plot.setLabel('bottom', 'Category')
plot.setLogMode(y=True)

# Set the y-axis limits (adjust as needed)
plot.setYRange(1, 1e8)

# Create a bar graph
bar = pg.BarGraphItem(x=x_values, height=y_values, width=0.6)
plot.addItem(bar)

# Show the plot
win.show()
app.exec_()
