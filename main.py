import os
# os.environ["QT_API"] = "pyside6"
# os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
# os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import traceback
from PySide6 import QtGui
import glob
import signal
import subprocess
import platform
from utils.logger import logger
import threading
import time
from screens import screens
from settings import INIT_SCREEN, APP_DIR, CRASH_FILE
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer
from ui.ui_main import Ui_Main
from functools import partial

class RFIDReaderApp(QMainWindow):

    _cur_screen = None
    _cur_screen_name = ""
    _snackbar = None
    EXIT_CODE_CRASH = -12345678

    def __init__(self):
        super().__init__()
        self.ui = Ui_Main()
        self.ui.setupUi(self)
        for k in {"overview", "settings"}:
            getattr(self.ui, f"btn_{k}").released.connect(
                partial(self.switch_screen, k)
            )
        self.switch_screen(INIT_SCREEN)
    
    def switch_screen(self, screen_name, **kwargs):
        if self._cur_screen_name == screen_name:
            return
        if self._cur_screen:
            self._cur_screen.on_leave()
            self.ui.stack.removeWidget(self._cur_screen)
        self._cur_screen = (
            screens[screen_name](app=self, **kwargs) if screen_name in screens else None
        )
        self._cur_screen_name = screen_name
        if self._cur_screen:
            self.ui.stack.addWidget(self._cur_screen)
            self.ui.stack.setCurrentWidget(self._cur_screen)
            logger.info(f"Added {screen_name} screen to stack widget")
        else:
            logger.error(f"Failed to create {screen_name} screen")
            
        for k in screens.keys():
            sh = (
                "color:#FFFFFF;background-color:#595959;border-top-right-radius:5px;border-top-left-radius:5px;padding-left:10px"
                if k == self._cur_screen_name
                else "color:#FFFFFF;border:none;"
            )
            getattr(self.ui, f"btn_{k}").setStyleSheet(sh)
        logger.info(f"Switched to {screen_name} screen")

if __name__ == "__main__":

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, exc_tb):
        msg = f"Exctype: {exctype}, Value: {value}\nTraceback:\n {','.join(traceback.format_tb(exc_tb, limit=20))}"
        logger.error(f"!!!! Crashed! {msg}")
        with open(CRASH_FILE, "w") as f:
            f.write(msg.replace("\\n", "\n"))
        getattr(sys, "_excepthook")(exctype, value, exc_tb)
        QApplication.exit(RFIDReaderApp.EXIT_CODE_CRASH)

    sys.excepthook = exception_hook

    # Run network initialization command before app starts
    try:
        if platform.system() == "Linux":
            result = subprocess.run(["sudo", "-n", "dhclient", "usb0"], capture_output=True, text=True, timeout=20)
            logger.info(f"Executed 'sudo dhclient usb0' (rc={result.returncode})")
            if result.stdout:
                logger.info(result.stdout.strip())
            if result.stderr:
                logger.warning(result.stderr.strip())
        else:
            logger.info("Skipping 'sudo dhclient usb0' (non-Linux platform)")
    except Exception as e:
        logger.error(f"Error executing 'sudo dhclient usb0': {e}")

    # Enable GPS on startup
    try:
        from utils.common import enable_gps_at_command
        logger.info("Attempting to enable GPS on application startup...")
        enable_gps_at_command()
    except Exception as e:
        logger.error(f"Error enabling GPS on startup: {e}")

    logger.info("========== Starting Kiosk App ==========")

    # Try different Qt platforms for Raspberry Pi
    app = QApplication(sys.argv)

    # Register fonts
    for font in glob.glob(os.path.join(APP_DIR, "font", "*.ttf")):
        QtGui.QFontDatabase.addApplicationFont(font)

    cur_exit_code = RFIDReaderApp.EXIT_CODE_CRASH

    while cur_exit_code == RFIDReaderApp.EXIT_CODE_CRASH:
        rm_form = RFIDReaderApp()
        rm_form.show()
        cur_exit_code = app.exec()
        rm_form.close()
