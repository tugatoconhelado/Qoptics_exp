import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QLabel
import os
import PySide2
os.environ['QT_MAC_WANTS_LAYER'] = '1'

print(PySide2.__version__)
# Create the application
app = QApplication(sys.argv)

# Create the main window
window = QMainWindow()
window.setWindowTitle("My GUI")

# Create a label widget
label = QLabel("Hello, World!")
window.setCentralWidget(label)

# Show the window
window.show()
window.raise_()

# Start the event loop
sys.exit(app.exec_())
