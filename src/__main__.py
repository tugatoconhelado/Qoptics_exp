import sys
from QuDX.experiments.timetrace import TimeTrace
from PySide2.QtWidgets import QApplication


def exec_timetrace():

    app = QApplication([])
    timetrace = TimeTrace()
    timetrace.initialise()
    sys.exit(app.exec_())

if __name__ == '__main__':
    exec_timetrace()