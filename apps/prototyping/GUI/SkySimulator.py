# Main stuff
import collections
import json
import logging.config
import os
import sys
import threading

# Numerical stuff
import numpy as np

# QT stuff
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QDockWidget
from PyQt5.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QVector3D
from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
from PyQt5.QtCore import Qt, QThread, pyqtSlot

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.utils.iers import conf
#conf.auto_max_age = None

# Local stuff: rendering tools
from ScopeSimulator import World3D

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService
from ScopeSimulator.View3D import View3D

class MainWindow(QMainWindow):
    def __init__(self, view3D):
        super().__init__()

        # Various views/widgets
        self.view3D = view3D

        # Change visual parameters and setup widgets on the main window
        self.resize(2048, 1024)#, 480)
        self.init_UI()

    def init_UI(self):
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
            statusTip="Exit the application", triggered=self.quit)
        self.aboutAct = QAction("&About", self,
                    statusTip="Show the application's About box",
                    triggered=self.about)
        self.creditsAct = QAction("&Credits", self,
                    statusTip="Show the application's Credits box",
                    triggered=self.credits)
        self.aboutQtAct = QAction("About &Qt", self,
                    statusTip="Show the Qt library's About box",
                    triggered=QApplication.instance().aboutQt)

        self.testMenu = self.menuBar().addMenu("&Settings")
        self.testMenu.addAction(self.exitAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("A&bout")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)
        self.helpMenu.addAction(self.creditsAct)

        # General layout
        self.layout = QVBoxLayout()

        # 3D view
        #self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_view3D)
        self.widget3D = QWidget.createWindowContainer(self.view3D.window, self)
        #self.widget3D.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #self.dock_view3D.setWidget(self.widget3D)
        self.setCentralWidget(self.widget3D)
        #self.layout.addWidget(self.widget3D)

        # Global stuff
        self.setLayout(self.layout)
        self.setWindowTitle('Remote observatory dashboard')
        self.show()

    def closeEvent(self, event):
        self.quit()

    def quit(self):
        self.close()

    def credits(self):
        QMessageBox.about(self, 'Credits',
                '<ul><li>Compass image from <a href="https://commons.wikimedia.org/wiki/File:Compass_Card_B%2BW.svg">wikimedia</a>'
                '<small> By Original: Denelson83 Derivative work: smial '
                'This file was derived from:  Compass Card.svg) <a href="http://www.gnu.org/copyleft/fdl.html">GFDL</a> or <a href="http://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA-3.0</a>, via Wikimedia Commons</li>'
                '<li>Bright star catalog used to display stars from <a href="ftp://cdsarc.u-strasbg.fr/cats/V/50/">CDS</a></li>'
                '<li>Qt5 from <a href="https://www.qt.io/">qt.io</a> and PyQt5 from <a href="https://www.riverbankcomputing.com/">RiverBank Computing</a></li></ul>'
                )

    def about(self):
        QMessageBox.about(self, 'Mount 3D Demo',
                'This demo shows an equatorial mount'
                'connected to an INDI Telescope.'
                'It will follow every move as reported'
                'by the INDI telescope driver.')

class GuiLoop():

    def __init__(self, gps_coord, observatory, serv_time):
        self.gps_coord = gps_coord
        self.observatory = observatory
        self.serv_time = serv_time

    def run(self):
        app = QApplication([])

        # Initialize various widgets/views
        view3D = View3D(serv_time=self.serv_time)

        # Now initialize main window
        self.main_window = MainWindow(view3D=view3D)

        self.main_window.view3D.set_coord(self.gps_coord)
        self.main_window.view3D.initialise_camera()
        self.main_window.view3D.window.show()

        # Everything ends when program is over
        status = app.exec_()
        sys.exit(status)

    # callback for updating model
    def update_coord(self, coord):
        self.main_window.view3D.model.setHA(coord['RA'])
        self.main_window.view3D.model.setDEC(coord['DEC'])

if __name__ == "__main__":

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # Build the observatory
    obs = ShedObservatory()
    serv_time = NTPTimeService()
    gps_coord = obs.getGpsCoordinates()
    main_loop = GuiLoop(gps_coord=gps_coord, observatory=obs,
                        serv_time=serv_time)
    main_loop.run()

# Launch through web ? Doesn't work at the moment...
# QT_QPA_PLATFORM=webgl:port=8998 PYTHONPATH=. python ./apps/prototyping/GUI/SkySimulator.py
