# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

# PyQt5 stuff
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFrame, QVBoxLayout

class DashboardWidget(QFrame):

    def __init__(self, parent=None, url='https://pythonspot.com'):
        super(QFrame, self).__init__(parent)
        self.url = url
        self.init_UI()

    def init_UI(self):
        #self.dockWidgetContents = QtWidgets.QWidget()
        #self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.webEngineView = QtWebEngineWidgets.QWebEngineView(self)
        #    self.dockWidgetContents)
        #self.webEngineView.setGeometry(QtCore.QRect(0, 20, 451, 331))
        self.webEngineView.setUrl(QtCore.QUrl(self.url))
        self.webEngineView.setObjectName("webEngineView")
        self.webEngineView.show()
        #self.lineEdit = QtWidgets.QLineEdit(self.dockWidgetContents)
        #self.lineEdit.setGeometry(QtCore.QRect(0, 0, 451, 23))
        #self.lineEdit.setObjectName("lineEdit")

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.webEngineView, Qt.AlignCenter)
        #layout.addWidget(self.lineEdit, Qt.AlignCenter)
        self.setLayout(layout)

        #self.retranslateUi(DockWidget)
        #QtCore.QMetaObject.connectSlotsByName(DockWidget)

    #def retranslateUi(self, DockWidget):
    #    _translate = QtCore.QCoreApplication.translate
    #    DockWidget.setWindowTitle(_translate("DockWidget", "DockWidget"))

from PyQt5 import QtWebEngineWidgets

