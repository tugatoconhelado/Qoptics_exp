import sys
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox, QPushButton, QLabel, QMessageBox
)
from 

class HUD(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the main layout
        self.setWindowTitle("Stepper Motor Controller")
        self.setGeometry(300, 300, 400, 150)

        layout = QVBoxLayout()

        # Add dropdown lists (QComboBox)
        self.dropdown_1 = QComboBox()
        self.dropdown_1.addItems(["Forward", "Backward"])

        self.dropdown_2 = QComboBox()
        self.dropdown_2.addItems(["1", "10", "100", "1000"])

        # Add labels and dropdowns to the layout
        layout.addWidget(QLabel("Choose Direction"))
        layout.addWidget(self.dropdown_1)

        layout.addWidget(QLabel("Choose Number of Steps:"))
        layout.addWidget(self.dropdown_2)

        # Add a button that triggers some action
        action_button = QPushButton("Initialize Action")
        action_button.clicked.connect(self.initialize_action)

        layout.addWidget(action_button)

        # Set the main layout to the window
        self.setLayout(layout)


    def initialize_action(self):
        # Get the current selections from the dropdowns
        self.direction = self.dropdown_1.currentText()
        self.steps = int(self.dropdown_2.currentText())

        self.call_backend(self.direction, self.steps)

    def show_message(self, message):
        # Show a message box with the result
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.exec_()        




if __name__ == "__main__":
    # Check if a QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    hud = HUD()
    hud.show()

    sys.exit(app.exec_())