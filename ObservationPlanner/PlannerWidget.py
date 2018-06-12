# Global stuff
import sys
import logging
from datetime import timedelta

# PyQt stuff
from PyQt5.QtWidgets import QWidget, QApplication, QFrame
from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from PyQt5.QtCore import QObject, QRunnable, Qt,QThreadPool
from PyQt5.QtCore import pyqtSlot, pyqtSignal

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
    def __init__(self, parent=None, observatory=None, serv_time=None,
                 logger=None):
        super(QFrame, self).__init__(parent)
        self.logger = logger or logging.getLogger(__name__)

        # a figure instance to plot on
        self.figure = plt.figure(figsize=(20,6))#6 should work

        # Observatory needed
        self.observatory = observatory
        # ntp time server
        self.serv_time = serv_time
        # ObservationPlanner
        self.obs_planner = ObservationPlanner(ntpServ=serv_time,
                                              obs=observatory)

        # Init a ThreadPool for asynchronous worloads
        self.threadpool = QThreadPool()
        self.logger.debug('Initialize threadpool to serve UI requests with '
                          'a maximum of {} threads'.format(
                          self.threadpool.maxThreadCount))

        self.init_UI()

    def init_UI(self):
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.plan_button = QPushButton('Plan observation')
        self.plan_button.clicked.connect(self.launch_plan)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar,Qt.AlignCenter)
        layout.addWidget(self.canvas, Qt.AlignCenter)
        layout.addWidget(self.plan_button)
        self.setLayout(layout)

    def plot(self):
        # refresh canvas
        self.canvas.draw()

    def finished_planning(self):
        self.logger.debug("Planning task completed")

    @pyqtSlot()
    def launch_plan(self, start_time=None, duration_hour=None):
        #print('Target list is {}'.format(obs_planner.getTargetList()))
        worker = Worker(lambda : self.plan(start_time, duration_hour))
        worker.signals.result.connect(self.plot)
        worker.signals.finished.connect(self.finished_planning)
        self.threadpool.start(worker)

    def plan(self, start_time=None, duration_hour=None):
        # Now schedule with astroplan
        self.obs_planner.init_schedule(start_time, duration_hour)
        self.obs_planner.showObservationPlan(start_time,
                                             duration_hour,
                                             show_plot=False,
                                             write_plot=False,
                                             afig=self.figure)
        
        tm = self.serv_time.getNextLocalMidnightInUTC()
        tm = tm + timedelta(hours=-5)
        self.obs_planner.annotate_time_point(time_point=tm)

class WorkerSignals(QObject):
    '''
        Defines the signals available from a running worker thread.
        Supported signals are:
        finished
            No data
        error
            `tuple` (exctype, value, traceback.format_exc() )
        result
            `object` data returned from processing, anything
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QRunnable):
    '''
        Worker thread
        Inherits from QRunnable to handler worker thread setup, signals and w
        :param callback: The function callback to run on this worker thread.
        kwargs will be passed through to the runner.
        :type callback: function
        :param args: Arguments to pass to the callback function
        :param kwargs: Keywords to pass to the callback function
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
          Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)

        try:
            result = self.fn(
                *self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exception()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
