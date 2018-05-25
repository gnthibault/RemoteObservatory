# Main stuff
import os
import sys
import collections
import json

# QT stuff
from PySide2 import QtCore, QtGui, QtNetwork, QtWidgets

# Pivy stuff, conda config --add channels conda-forge + conda install pyside2
from pivy.coin import SoInput, SoDB
from pivy.quarter import QuarterWidget

import os, sys
sys.path.append(os.path.join(os.environ["CONDA_PREFIX"], "lib"))

# Local stuff
import Simulator

class SliderPreciseValue(QtWidgets.QFrame):

    valueChanged = QtCore.Signal(int)

    def changeValue(self, v):
        """
           Everytime the value is changed, either through Gui or through an API,
           the signal updates the qslider, and forward the value v (from 0 to 1)
           as a new signal: valueChanged
        """
        self.qlcd.display(v)
        if self.sender != self.qslider:
            self.qslider.setValue(int(v))
        self.valueChanged.emit(int(v))

    def __init__(self, label, digits, minmax, wrap, toggable, lineeditlength,
                 regexpstring=None, tooltip=None):
        """
            This whole class purpose is to define multiple fancy gui items
            (buttons, user inputs, slider) in order to set a single value
        """

        #Init parent QFrame
        QtWidgets.QFrame.__init__(self)
        self.setFrameShape(QtWidgets.QFrame.Box)

        #Define the layout elements (labels, lcd, input, etc...)
        self.qboxlayout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight, self)

        # Show a label that describes the current qBox
        self.qlabel = QtWidgets.QLabel(label)

        # Show current value with a lcd
        self.qlcd = QtWidgets.QLCDNumber(digits)
        self.qlcd.setFixedHeight(16)
        self.qlcd.setStyleSheet(
            "QFrame {background-color: black; color: red; }")
        self.qlcd.setSegmentStyle(QtWidgets.QLCDNumber.Filled)

        # Add a slider: a knob to be turned from 0 to 1 (it goes to 11 !!!)
        self.qslider = QtWidgets.QDial()
        self.qslider.setFixedHeight(30)
        self.qslider.setWrapping(wrap)
        self.qslider.setMinimum(minmax[0])
        self.qslider.setMaximum(minmax[1])

        # Configure user input box, with a regexp for input values
        self.qlineedit = QtWidgets.QLineEdit()
        if regexpstring != None:
            self.qlineedit.setValidator(QtGui.QRegExpValidator(
                QtCore.QRegExp(regexpstring)))
        self.qlineedit.sizeHint=lambda:QtCore.QSize((lineeditlength*10),14)
        if tooltip != None:
            self.qlineedit.setToolTip(tooltip)

        # Add a button to validate the user input
        self.qbutton=QtWidgets.QPushButton('Set')
        self.qbutton.sizeHint=lambda:QtCore.QSize((30),24)

        # Each qbox contains label+lcd+slider+input+button
        self.qboxlayout.addWidget(self.qlabel)
        self.qboxlayout.addWidget(self.qlcd)
        self.qboxlayout.addWidget(self.qslider)
        self.qboxlayout.addWidget(self.qlineedit)
        self.qboxlayout.addWidget(self.qbutton)

        # Connect the slider to the slot that actually do something with the
        # value
        self.qslider.valueChanged.connect(self.changeValue)
        # Finishing edition has the same effect as hitting the button
        self.qlineedit.editingFinished.connect(self.qbutton.click)
        # The button also forward value to the main signal
        self.qbutton.clicked.connect(
            lambda:self.changeValue(float(self.qlineedit.text())))

        # it should look nice like that
        self.qboxlayout.setContentsMargins(QtCore.QMargins(5, 0, 5, 0))
        self.sizeHint=lambda:QtCore.QSize(260,70)
        self.show()


class ManualSettingDockWidget(QtWidgets.QDockWidget):
    """
        This widget will group multiple precise slider (qbox), each related to a
        single parameter of the application (ra, dec, ...)

        It is also in charge of connecting signals from the qboxes to actual
        useful functions in the backend of the simulator
    """
    def __init__(self, simulator):
        # Init stuff so that it looks nice
        self.dockwidget = QtWidgets.QDockWidget.__init__(self,
            QtCore.QCoreApplication.translate("ManualSettingDockWidget",
                                              "Manual Settings"))
        self.setStyleSheet("QFrame, QLineEdit, QPushButton, QCheckBox "
                           "{font-size: 8pt;}\n")
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | 
                             QtCore.Qt.BottomDockWidgetArea)
        self.content = QtWidgets.QWidget()
        self.content.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                   QtWidgets.QSizePolicy.Maximum)

        # The important Backend object
        self.simulator = simulator
        self.qgridlayout = QtWidgets.QGridLayout( self.content)

        # Define all the important boxes (1 parameter per box)

        # Box 1: The slider to select latitude for eq mount
        self.latitudeSPV = SliderPreciseValue(
            QtCore.QCoreApplication.translate("ManualSettingDockWidget",
                "Latitude"),
            7, (-90.00, 90.00), False, False, 8, '-?\\d{1,2}(\.\\d{1,4})?',
            'Enter Latitude in decimal format, negative for South hemisphere')
        self.latitudeSPV.valueChanged.connect(self.simulator.setLatitude)
        self.qgridlayout.addWidget(self.latitudeSPV, 0, 0)

        # Box 2: only a checkbox for setting the hemisphere
        self.hemisphereframe=QtWidgets.QFrame()
        self.hemisphereframe.setFrameShape(QtWidgets.QFrame.Box)
        self.hemispherecheckbox=QtWidgets.QCheckBox('Southern Hemisphere',
            self.hemisphereframe)
        self.hemispherecheckbox.setContentsMargins(4,4,4,4)
        self.hemispherecheckbox.setCheckState(QtCore.Qt.Unchecked)
        self.hemispherecheckbox.setCheckable(False)
        self.qgridlayout.addWidget(self.hemisphereframe, 1, 0)

        # Box 3: The ra-angle
        self.raangleSPV = SliderPreciseValue(
            QtCore.QCoreApplication.translate("ManualSettingDockWidget", "RA Angle"),
            8, (0.00, 360.00), True, False, 8,
            '(([0-2]?\\d{1,2})|(3[0-5][0-9]))(\.\\d{1,4})?',
            'Enter RA axis angle in decimal degrees')
        self.raangleSPV.valueChanged.connect(self.simulator.setRAangle)
        self.qgridlayout.addWidget(self.raangleSPV, 0, 1)

        # Box 4: The de-angle
        self.deangleSPV = SliderPreciseValue(
            QtCore.QCoreApplication.translate("ManualSettingDockWidget", "DE Angle"),
            8, (0.00, 360.00), True, False, 8,
            '(([0-2]?\\d{1,2})|(3[0-5][0-9]))(\.\\d{1,4})?',
            'Enter DE axis angle in decimal degrees')
        self.deangleSPV.valueChanged.connect(self.simulator.setDEangle)
        self.qgridlayout.addWidget(self.deangleSPV, 1, 1)

        # Box 5: The focuser position
        self.focuserpositionSPV = SliderPreciseValue(
            QtCore.QCoreApplication.translate("ManualSettingDockWidget", "Foc. pos."),
            6, (0.00, 120.00), True, False, 8,
            '((0?\\d{1,2})|(1[0-1][0-9]))(\.\\d{1,4})?',
            'Enter Focuser position in millimeters')
        self.focuserpositionSPV.valueChanged.connect(
            self.simulator.setFocuserposition)
        self.qgridlayout.addWidget(self.focuserpositionSPV, 0, 2)

        # Box 6: The focuser angle
        self.focuserangleSPV=SliderPreciseValue(
            QtCore.QCoreApplication.translate("ManualSettingDockWidget", "Foc. ang."),
            6, (0.00, 360.00), True, False, 8,
            '(([0-2]?\\d{1,2})|(3[0-5][0-9]))(\.\\d{1,4})?',
            'Enter Focuser angle in decimal degrees')
        self.focuserangleSPV.valueChanged.connect(
            self.simulator.setFocuserangle)
        self.qgridlayout.addWidget(self.focuserangleSPV, 1, 2)

        # Now show everything
        self.content.show()
        self.setWidget(self.content)

class LcdArray(QtWidgets.QScrollArea):
    """
        This class is only used to define a small lcd screen that allows to
        show backend informations to the user
    """
    def __init__(self, valuelist):
        QtWidgets.QScrollArea.__init__(self)
        self.setStyleSheet("QFrame  {font-size: 8pt;}\n")
        self.qgridlayout = QtWidgets.QGridLayout( self)
        self.dictionnary = dict()
        lcdrecord = collections.namedtuple('LcdRecord',
                                           ['name', 'qlabel', 'qlcd'])
        # For each backend value, define a lcd
        for  index, (name, label, digits, mode) in enumerate(valuelist):
            qlabel = QtWidgets.QLabel(label, self)
            qlcd = QtWidgets.QLCDNumber(digits)
            qlcd.setFixedHeight(16)
            lcdmode = QtWidgets.QLCDNumber.Dec
            if (mode=='H'):
                lcdmode = QtWidgets.QLCDNumber.Hex 
            elif (mode=='B'):
                lcdmode=QtWidgets.QLCDNumber.Bin
            qlcd.setMode(lcdmode)
            qlcd.setStyleSheet("QFrame {background-color: black; color: red; }")
            r = lcdrecord(name, qlabel, qlcd)
            self.dictionnary[name] = r
            # Add the label and the actual lcd to the qgrid
            self.qgridlayout.addWidget(r.qlabel, index, 0)
            self.qgridlayout.addWidget(r.qlcd, index, 1)
        self.show()

    def setValue(self, name, value):
        self.dictionnary[name].qlcd.display(value)

class ValueInfoDockWidget(QtWidgets.QDockWidget):
    """
        This class intends to show some read-only values that comes from
        the backend
    """
    def __init__(self):
        QtWidgets.QDockWidget.__init__(self,
            QtCore.QCoreApplication.translate("ValueInfoDockWidget", 
            "BackendInfos"))
        self.setStyleSheet(
            "QFrame, QLineEdit, QPushButton, QCheckBox {font-size: 8pt;}\n")

        # Stick it somewhere
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea |
                             QtCore.Qt.RightDockWidgetArea)
        self.tabwidget = QtWidgets.QTabWidget(self)

        #self.ralcd=LcdArray([('RA_STEPS_360','Tot. steps', 8, 'H'),
        #    ('ra_position', 'Cur. step', 8, 'H')])
        #self.delcd=LcdArray([('DE_STEPS_360', 'Tot. steps', 8, 'H'),
        #    ('de_position','Cur. step', 8, 'H')])
        #self.tabwidget.addTab(self.ralcd, "RA Stepper")
        #self.tabwidget.addTab(self.delcd, "DE Stepper")

        # Show everything
        self.tabwidget.show()

class SimulationFrameWidget(QtWidgets.QWidget):
    """
        This class intends to show some read-only values that comes from
        the backend
    """
    def __init__(self, simulator):
        QtWidgets.QWidget.__init__(self)
        self.simulator = simulator
        self.setMinimumSize(712,400)
        self.qw = QuarterWidget(self)
        self.qw.setMinimumSize(712, 400)
        self.qw.setSceneGraph(self.simulator.scene)

def main():
    try:
        import FreeCAD
    except ValueError:
        raise RuntimeError('FreeCAD library not found. Please check that the '
                           'FREECADPATH variable in this script is correct')
        
    simapp = QtWidgets.QApplication(sys.argv)
    simappwindow = QtWidgets.QMainWindow()
    simappwindow.setWindowTitle("EQ Simulator")

    # Build the backend
    s = Simulator.Simulator()
    s.Build()

    # Build manual setting widget
    manualsettingswidget = ManualSettingDockWidget(s)

    # Build the info widget
    valueinfowidget = ValueInfoDockWidget()

    # Build the simulated system frame, that is generated by the backend,
    # through freecad
    widget3D = SimulationFrameWidget(s)

    # Add all widgets to main application window
    simappwindow.addDockWidget(QtCore.Qt.BottomDockWidgetArea,
                               manualsettingswidget)
    simappwindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea,
                               valueinfowidget)
    simappwindow.setCentralWidget(widget3D)


    # Now show everything
    simappwindow.show()
    simapp.exec_() 

if __name__ == "__main__":
    main()
