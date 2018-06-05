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
from PyQt5.QtCore import Qt, QThread

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

# Local stuff
sys.path.append('.')

sys.path.append('ScopeSimulator')
from ScopeSimulator import View3D

# Local stuff : IndiClient
from helper.Indi3DSimulatorClient import Indi3DSimulatorClient

# Local stuff : Mount
from Mount.IndiMount import IndiMount

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff: Observation planner Widget
from ObservationPlanner.PlannerWidget import AltazPlannerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1024, 480)
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
        #self.dock_view3D = QDockWidget('Mount simulator', self)
        self.view3D = View3D.View3D()
        self.widget3D = QWidget.createWindowContainer(self.view3D.window)
        #self.widget3D.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #self.dock_view3D.setWidget(self.widget3D)
        self.setCentralWidget(self.widget3D)
        #self.layout.addWidget(self.dock_view3D)

        # Dock planner
        self.dock_planner = QDockWidget('Observation planner', self)
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock_planner)
        self.planner = AltazPlannerWidget() #observatory=)
        #self.planner.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.dock_planner.setWidget(self.planner)
        self.planner.plot()

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

class GuiLoop(threading.Thread):

    def __init__(self, gps_coord, mount):
        threading.Thread.__init__(self)
        self.gps_coord = gps_coord
        self.mount = mount

    def __del__(self):
        print('Main Qt thread is going to exit')

    def run(self):
        app = QApplication([])
        self.main_window = MainWindow()

        indiCli.register_number_callback(
            device_name = self.mount.deviceName,
            vec_name = 'EQUATORIAL_EOD_COORD',
            callback = self.update_coord)

        self.main_window.view3D.set_coord(self.gps_coord)
        self.main_window.view3D.initialiseCamera()
        self.main_window.view3D.window.show()
        sys.exit(app.exec_())

    # callback for updating model
    def update_coord(self, coord):
        self.main_window.view3D.model.setHA(coord['RA'])
        self.main_window.view3D.model.setDEC(coord['DEC'])

if __name__ == "__main__":

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # build+connect indi client
    indiCli = Indi3DSimulatorClient(None)
    indiCli.connect()

    # Build the observatory
    obs = ShedObservatory()

    # Build the Mount
    mount = IndiMount(indiClient=indiCli,
                      configFileName=None, connectOnCreate=True)
    gps_coord = obs.getGpsCoordinates()

    thread = GuiLoop(gps_coord, mount)
    thread.start()
    
    # Now start to do stuff
    mount.set_slew_rate('SLEW_FIND')

    # Unpark if you want something useful to actually happen
    mount.unPark()

    # Do a slew and track
    c = SkyCoord(ra=0.5*u.hour, dec=5*u.degree, frame='icrs')
    mount.slew_to_coord_and_track(c)

    # Sync
    c = SkyCoord(ra=0.5*u.hour, dec=5*u.degree, frame='icrs')
    mount.sync_to_coord(c)

    #Do a slew and stop
    c = SkyCoord(ra=10*u.hour, dec=60*u.degree, frame='icrs')
    mount.slew_to_coord_and_stop(c)

    # Park before standby
    mount.park()

    # Everything ends when program is over
    thread.join()
