# Embedded file name: ..\Resources\turn_on_toolkit.py
from PySide import QtGui
from .ui import turn_on_toolkit

class TurnOnToolkit(QtGui.QDialog):

    def __init__(self, connection, login, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = turn_on_toolkit.Ui_TurnOnToolkit()
        self.ui.setupUi(self)
        self._login = login
        self.addAction(self.ui.actionClear_login_data)
        self.ui.actionClear_login_data.triggered.connect(self.clear_login_data)
        url_text = "<a href='%s/page/manage_apps'><span style='font-size:20pt; text-decoration: underline; color:#f0f0f0;'>Manage Apps</span></a>" % connection.base_url
        self.ui.url_label.setText(url_text)

    def clear_login_data(self):
        self._login._clear_saved_values()
        self._login._clear_password()
        self.reject()