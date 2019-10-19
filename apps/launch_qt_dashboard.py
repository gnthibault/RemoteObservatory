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
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.utils.iers import conf
conf.auto_max_age = None

# Local stuff: rendering tools
from ScopeSimulator import View3D

# Local stuff: Dashboard widget
from Dashboard.CameraWidget import CameraWidget
from Dashboard.DashboardWidget import DashboardWidget

# Local stuff: get actual config
from utils import load_module
from utils.config import load_config

# Local stuff : IndiClient
from helper.Indi3DSimulatorClient import Indi3DSimulatorClient

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService


class MainWindow(QMainWindow):

    closing = pyqtSignal()
 
    def __init__(self, view3D=None, camera_widget=None, dashboard_widget=None):
        super().__init__()

        # Various views/widgets
        self.view3D = view3D
        self.camera_widget = camera_widget
        self.closing.connect(self.camera_widget.close)
        self.dashboard_widget = dashboard_widget

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
        #self.layout = QVBoxLayout()

        # Webbrowser for dashboard should be the main widget
        if self.dashboard_widget is not None:
            #self.dock_dashboard = QDockWidget('Main dashboard', self)
            #self.addDockWidget(Qt.RightDockWidgetArea, self.dock_dashboard)
            #self.dashboard_widget.setSizePolicy(QSizePolicy.Fixed,
            #                                    QSizePolicy.Fixed)
            #self.dock_dashboard.setWidget(self.dashboard_widget)
            self.setCentralWidget(self.dashboard_widget)

        # Dock safety camera on the Left
        if self.camera_widget is not None:
            self.dock_camera = QDockWidget('Surveillance camera', self)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_camera)
            #self.camera_widget.setSizePolicy(QSizePolicy.Fixed,
            #                                 QSizePolicy.Fixed)
            self.dock_camera.setWidget(self.camera_widget)

        # 3D view set as right widget
        if self.view3D is not None:
            self.widget3D = QWidget.createWindowContainer(self.view3D.window)
            self.dock_view3D = QDockWidget('Mount simulator', self)
            self.addDockWidget(Qt.RightDockWidgetArea, self.dock_view3D)
            #self.widget3D.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.dock_view3D.setWidget(self.widget3D)
            #self.setCentralWidget(self.widget3D)
            #self.layout.addWidget(self.widget3D)

        # Global stuff
        #self.setLayout(self.layout)
        self.setWindowTitle('Remote observatory dashboard')
        self.show()

    def closeEvent(self, event):
        # emit a signal for registered custom slot to perform cleanup if needed
        self.closing.emit()
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

    def __init__(self, serv_time, gps_coord, mount):
        self.gps_coord = gps_coord
        self.mount = mount
        self.serv_time = serv_time

    def run(self):
        app = QApplication([])

        # Initialize various widgets/views
        view3D = View3D.View3D(serv_time=self.serv_time)
        camera_widget = CameraWidget(url=0)
        dashboard_widget = DashboardWidget(url='http://localhost:8888')

        # Now initialize main window
        self.main_window = MainWindow(view3D=view3D,
                                      camera_widget=camera_widget,
                                      dashboard_widget=dashboard_widget)

        indi_client.register_number_callback(
            device_name = self.mount.device_name,
            vec_name = 'EQUATORIAL_EOD_COORD',
            callback = self.update_coord)

        self.main_window.view3D.set_coord(self.gps_coord)
        self.main_window.view3D.initialiseCamera()
        self.main_window.view3D.window.show()

        # Everything ends when program is over
        status = app.exec_()
        sys.exit(status)

    # callback for updating model
    def update_coord(self, coord):
        self.main_window.view3D.model.setHA(coord['RA'])
        self.main_window.view3D.model.setDEC(coord['DEC'])

if __name__ == "__main__":

    def trap_exc_during_debug(*args):
        # when app raises uncaught exception, print info
        print(args)

    # install exception hook: without this, uncaught exception would cause
    # application to exit
    sys.excepthook = trap_exc_during_debug

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # At this point, we are doing what Manager.Manager is doing

    # build+connect indi client
    config = load_config()
    indi_client = Indi3DSimulatorClient(config=config['indiclient'])
    indi_client.connect()

    # Build the observatory
    obs_name = config['observatory']['module']
    obs_module = load_module('Observatory.' + obs_name)
    obs = getattr(obs_module, obs_name)(
        config=config['observatory'])
    earth_location = obs.getAstropyEarthLocation()

    # ntp time server
    serv_time = NTPTimeService()

    # Build the Mount
    mount_name = config['mount']['module']
    mount_module = load_module('Mount.' + mount_name)
    mount = getattr(mount_module, mount_name)(
        indi_client=indi_client,
        location=earth_location,
        serv_time=serv_time,
        config=config['mount'])

    gps_coord = obs.getGpsCoordinates()

    main_loop = GuiLoop(serv_time, gps_coord, mount)
    main_loop.run()
