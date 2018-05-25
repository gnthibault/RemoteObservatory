#!/usr/bin/env python

import os
import sys

from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QMainWindow, QAction, QApplication, QMdiArea

from pivy.coin import SoInput, SoDB
from pivy.quarter import QuarterWidget

import os, sys
sys.path.append(os.path.join(os.environ["CONDA_PREFIX"], "lib"))
import FreeCADGui


class MdiQuarterWidget(QuarterWidget):
    def __init__(self, parent, sharewidget):
        QuarterWidget.__init__(self, parent=parent, sharewidget=sharewidget)

    def minimumSizeHint(self):
        return QtCore.QSize(640, 480)


class MdiMainWindow(QMainWindow):
    def __init__(self, qApp):
        QMainWindow.__init__(self)
        self._firstwidget = None
        self._mdiArea = QMdiArea()
        self.setCentralWidget(self._mdiArea)
        self.setAcceptDrops(True)
        self.setWindowTitle("Pivy Quarter MDI example")

        filemenu = self.menuBar().addMenu("&File")
        windowmenu = self.menuBar().addMenu("&Windows")

        fileopenaction = QAction("&Create Box", self)
        fileexitaction = QAction("E&xit", self)
        tileaction = QAction("Tile", self)
        cascadeaction = QAction("Cascade", self)

        filemenu.addAction(fileopenaction)
        filemenu.addAction(fileexitaction)
        windowmenu.addAction(tileaction)
        windowmenu.addAction(cascadeaction)

        fileopenaction.triggered.connect(self.createBoxInFreeCAD)
        fileexitaction.triggered.connect(self._mdiArea.closeAllSubWindows)
        tileaction.triggered.connect(self._mdiArea.tileSubWindows)
        cascadeaction.triggered.connect(self._mdiArea.cascadeSubWindows)

        windowmapper = QtCore.QSignalMapper(self)
        windowmapper.mapped.connect(self._mdiArea.setActiveSubWindow)
        self.dirname = os.curdir       

    def closeEvent(self, event):
        self._mdiArea.closeAllSubWindows()

    def createBoxInFreeCAD(self):
        d=FreeCAD.newDocument()
        o=d.addObject("Part::Box")
        d.recompute()
        s=FreeCADGui.subgraphFromObject(o)
        child = self.createMdiChild()
        child.show()
        child.setSceneGraph(s)

    def createMdiChild(self):
        widget = MdiQuarterWidget(None, self._firstwidget)
        self._mdiArea.addSubWindow(widget)
        if not self._firstwidget:
            self._firstwidget = widget
        return widget


def main():
    app = QApplication(sys.argv)
    FreeCADGui.setupWithoutGUI()        
    mdi = MdiMainWindow(app)   
    mdi.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
