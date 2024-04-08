from PySide2.QtWidgets import QApplication, QDialog, QVBoxLayout, QSpinBox, QComboBox, QLabel, QMainWindow, QStackedWidget, QWidget, QHBoxLayout
from PySide2.QtCore import Slot

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super(MyDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.spinBoxes = [QSpinBox(self) for _ in range(5)]
        for spinBox in self.spinBoxes:
            self.layout.addWidget(spinBox)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.dialog = MyDialog(self)
        self.comboBox = QComboBox(self)
        self.comboBox.addItems([f'SpinBox {i+1}' for i in range(5)])
        self.comboBox.currentIndexChanged.connect(self.update_widget)
        self.stackedWidget = QStackedWidget(self)
        for spinBox in self.dialog.spinBoxes:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(spinBox)
            self.stackedWidget.addWidget(widget)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.comboBox)
        self.layout.addWidget(self.stackedWidget)
        self.centralWidget = QWidget(self)
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    @Slot(int)
    def update_widget(self, index):
        self.stackedWidget.setCurrentIndex(index)

app = QApplication([])
window = MainWindow()
window.show()
window.dialog.show()
app.exec_()
