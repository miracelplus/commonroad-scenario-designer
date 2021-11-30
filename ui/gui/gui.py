import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.gui.mwindow.mwindow import MWindow


def start_gui_new(input_file: str = None):
    """
    Redirect to the
    """
    # application
    app = QApplication(sys.argv)
    if input_file:
        w = MWindow(input_file)
    else:
        w = MWindow()
    w.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    start_gui_new()
