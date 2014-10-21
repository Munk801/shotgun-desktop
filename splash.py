# Embedded file name: ..\Resources\splash.py
from PySide import QtGui
from PySide import QtCore
from .ui import splash

class Splash(QtGui.QDialog):

    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = splash.Ui_Splash()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.WindowStaysOnTopHint)

    def set_message(self, text):
        self.ui.message.setText(text)
        QtGui.QApplication.instance().processEvents()