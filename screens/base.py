from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from utils.logger import logger
from widgets.lineedit import KioskLineEdit


class BaseScreen(QWidget):

    def __init__(self, app, **kwargs):
        super().__init__()
        self.app = app
        self.timeout = kwargs.get("timeout", 0)
        self.prev_screen = kwargs.get("prev_screen", "overview")
        QTimer.singleShot(50, self.on_enter)

    def on_enter(self):
        """
        This function is called by switch_screen() function in the main app.
        You can add anything to this function of a certain screen for initialization.
        :return:
        """
        pass

    def on_touched(self):
        """
        Used to support popup feature of the keyboard dialog.
        :return:
        """
        if (
            hasattr(self, "_keyboard_dlg") and
            getattr(self, "_keyboard_dlg") is not None
        ):
            getattr(self, "_keyboard_dlg").on_touched_screen()

    def on_leave(self):
        """Called when leaving the screen"""
        pass

    def is_valid(self):
        """
        Check if form widgets are valid
        :return:
        """
        for w in self.findChildren(KioskLineEdit):
            if w.isEnabled() and w.required:
                if not w.text():
                    logger.error(f"Please fill a field - `{w.objectName()}`")
                    w.mark_as_error()
                    return False
                elif w.is_numeric and float(w.text()) == 0:
                    logger.error(f"Please input correct value - `{w.objectName()}`")
                    w.mark_as_error()
                    return False
        return True

    def show_error_snackbar(self, msg="", duration=2):
        self.app.show_snackbar(msg=msg, msg_type="error", duration=duration)

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())
