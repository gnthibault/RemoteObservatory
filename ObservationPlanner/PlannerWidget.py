# Global stuff
import sys
import random #To be deleted later

# PyQt stuff
from PyQt5.QtWidgets import QWidget, QApplication, QFrame
from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSlot

# Matplotlib stuff
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff : observation planner
from ObservationPlanner.ObservationPlanner import ObservationPlanner


class AltazPlannerWidget(QFrame):
    def __init__(self, parent=None, observatory=None, serv_time=None):
        super(QFrame, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()

        # Observatory needed
        self.observatory = observatory
        # ntp time server
        self.serv_time = serv_time
        # ObservationPlanner
        self.obs_planner = ObservationPlanner(ntpServ=serv_time,
                                              obs=observatory)

        self.init_UI()

    def init_UI(self):
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to zoom_in/out method
        #self.zoom_in_button = QPushButton('Zoom in')
        #self.zoom_in_button.clicked.connect(self.zoom_in)
        #self.zoom_out_button = QPushButton('Zoom out')
        #self.zoom_out_button.clicked.connect(self.zoom_out)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar,Qt.AlignCenter)
        layout.addWidget(self.canvas, Qt.AlignCenter)
        #layout.addWidget(self.zoom_in_button)
        #layout.addWidget(self.zoom_out_button)
        self.setLayout(layout)

    def plot(self):
        ''' plot some random stuff '''
        # random data
        data = [random.random() for i in range(10)]

        # instead of ax.hold(False)
        self.figure.clear()

        # create an axis
        ax = self.figure.add_subplot(111)

        # plot data
        ax.plot(data, '*-')

        # refresh canvas
        self.canvas.draw()

    def plan(self, start_time=None, duration_hour=None):
        #print('Target list is {}'.format(obs_planner.getTargetList()))

        # Now schedule with astroplan
        obs_planner.init_schedule(start_time, duration_hour)
        afig, pfig = obs_planner.showObservationPlan(start_time, duration_hour,
                                                     show_plot=True,
                                                     write_plot=False)

    @pyqtSlot()
    def zoom_in(self):
        print('Zooming in')

    @pyqtSlot()
    def zoom_out(self):
        print('Zooming out')
