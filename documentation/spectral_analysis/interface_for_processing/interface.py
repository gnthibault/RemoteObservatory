
# Generic stuff
import os

# Pyqt stuff
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QMessageBox


# Local stuff
# interfaceui.py as been generated through: pyuic5 interfaceui.ui -x -o interfaceui.py
from interfaceui import Ui_MainWindow
from utils import log

class main_window(QtWidgets.QMainWindow):

    @log
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tFolder.setText(os.path.expanduser(Config.get_scan_folder_path()))
        self.ui.tDark.setText(os.path.expanduser(Config.get_dark_path()))
        self.ui.tWork.setText(os.path.expanduser(Config.get_work_folder_path()))

        self.running = False
        self.counter = 0
        self.align = False
        self.dark = False
        self.pause = False
        self.image_ref_save = image_ref_save()

        self.setWindowTitle(_("Astro Live Stacker") + f" - v{VERSION}")

        # web stuff
        self.thread = None
        self.web_dir = None

    @log
    def closeEvent(self, event):
        self._stop_www()

        try:
            Config.save()
            _logger.info("User configuration saved")
        except OSError as e:
            _logger.error(f"Could not save settings. Error : {e}")
            messaging.error_box("Settings not saved", f"Your settings could not be saved\n\nDetails : {e}")
        super().closeEvent(event)

    # ------------------------------------------------------------------------------
    # Callbacks