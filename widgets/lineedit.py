from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit


class KioskLineEdit(QLineEdit):
    """
    Customized LineEdit widget to use mouse pressed and focus events
    """

    mouse_pressed = Signal()
    focus_in = Signal()
    is_numeric = (
        False  # Flag to display the normal keyboard or numeric keyboard when pressed.
    )
    key = None  # Key of the widget to be used in form data
    required = True  # Flag to bypass validation or not.

    def __init__(self, parent):
        super().__init__(parent)
        self._init_style = "border: none; color: #FFFFFF; background-color: #181D3C;"

    def mark_as_error(self):
        self.setStyleSheet(self._init_style + "border: 2px solid #EE0000")

    def mark_as_normal(self):
        self.setStyleSheet(self._init_style)

    def mousePressEvent(self, event):
        self.mark_as_normal()
        getattr(self, "mouse_pressed").emit()

    def get_value(self):
        if self.text():
            return float(self.text()) if self.is_numeric else self.text()
        else:
            return 0 if self.is_numeric else ""

    def setText(self, text):
        if text is not None:
            self.mark_as_normal()
        return super().setText(str(text) if text is not None else "")

    def focusInEvent(self, arg__1) -> None:
        getattr(self, "focus_in").emit()
        super(KioskLineEdit, self).focusInEvent(arg__1)
