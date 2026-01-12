import math

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QStyle


class QtWaitingSpinner(QWidget):
    """
    Intuitive waiting spinner
    """

    def __init__(
        self,
        parent=None,
        center_on_parent=True,
        disable_parent_when_spinning=False,
        modality=QtCore.Qt.WindowModality.ApplicationModal,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog | QtCore.Qt.WindowType.FramelessWindowHint
        )
        self._center_on_parent = center_on_parent
        self._disableParentWhenSpinning = disable_parent_when_spinning

        # WAS IN initialize()
        self._color = QColor(QtCore.Qt.GlobalColor.green)
        self._roundness = 100.0
        self._minimumTrailOpacity = 3.14159265358979323846
        self._trailFadePercentage = 80.0
        self._revolutionsPerSecond = 1.57079632679489661923
        self._numberOfLines = 20
        self._lineLength = 15
        self._lineWidth = 3
        self._innerRadius = 15
        self._currentCounter = 0
        self._isSpinning = False

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.rotate)
        self.update_size()
        self.update_timer()
        self.hide()

        self.setWindowModality(modality)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        self.update_position()
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.GlobalColor.transparent)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        for i in range(0, self._numberOfLines):
            painter.save()
            painter.translate(
                self._innerRadius + self._lineLength,
                self._innerRadius + self._lineLength,
            )
            rotate_angle = float(360 * i) / float(self._numberOfLines)
            painter.rotate(rotate_angle)
            painter.translate(self._innerRadius, 0)
            distance = self.line_count_distance_from_primary(
                i, self._currentCounter, self._numberOfLines
            )
            color = self.current_line_color(
                distance,
                self._numberOfLines,
                self._trailFadePercentage,
                self._minimumTrailOpacity,
                self._color,
            )
            painter.setBrush(color)
            painter.drawRoundedRect(
                QtCore.QRect(
                    0, -self._lineWidth // 2, self._lineLength, self._lineWidth
                ),
                self._roundness,
                self._roundness,
                QtCore.Qt.SizeMode.RelativeSize,
            )
            painter.restore()

    def start(self):
        self.update_position()
        self._isSpinning = True
        self.show()

        if self.parentWidget and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(False)

        if not self._timer.isActive():
            self._timer.start()
            self._currentCounter = 0

    def stop(self):
        if not self._isSpinning:
            return

        self._isSpinning = False
        self.hide()
        if self.parentWidget() and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(True)
        if self._timer.isActive():
            self._timer.stop()
            self._currentCounter = 0

    #
    # def setNumberOfLines(self, lines):
    #     self._numberOfLines = lines
    #     self._currentCounter = 0
    #     self.updateTimer()
    #
    # def setLineLength(self, length):
    #     self._lineLength = length
    #     self.updateSize()
    #
    # def setLineWidth(self, width):
    #     self._lineWidth = width
    #     self.updateSize()
    #
    # def setInnerRadius(self, radius):
    #     self._innerRadius = radius
    #     self.updateSize()

    def color(self):
        return self._color

    def roundness(self):
        return self._roundness

    # def minimumTrailOpacity(self):
    #     return self._minimumTrailOpacity
    #
    # def trailFadePercentage(self):
    #     return self._trailFadePercentage
    #
    # def revolutionsPersSecond(self):
    #     return self._revolutionsPerSecond
    #
    # def numberOfLines(self):
    #     return self._numberOfLines
    #
    # def lineLength(self):
    #     return self._lineLength
    #
    # def lineWidth(self):
    #     return self._lineWidth
    #
    # def innerRadius(self):
    #     return self._innerRadius
    #
    # def isSpinning(self):
    #     return self._isSpinning
    #
    # def setRoundness(self, roundness):
    #     self._roundness = max(0.0, min(100.0, roundness))
    #
    # def setColor(self, color=QtCore.Qt.black):
    #     self._color = QColor(color)
    #
    # def setRevolutionsPerSecond(self, revolutionsPerSecond):
    #     self._revolutionsPerSecond = revolutionsPerSecond
    #     self.update_timer()
    #
    # def setTrailFadePercentage(self, trail):
    #     self._trailFadePercentage = trail
    #
    # def setMinimumTrailOpacity(self, minimumTrailOpacity):
    #     self._minimumTrailOpacity = minimumTrailOpacity

    def rotate(self):
        self._currentCounter += 1
        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0
        self.update()

    def update_size(self):
        size = (self._innerRadius + self._lineLength) * 2
        self.setFixedSize(size, size)

    def update_timer(self):
        self._timer.setInterval(
            1000 // int(self._numberOfLines * self._revolutionsPerSecond)
        )

    def update_position(self):
        if self.parentWidget() and self._center_on_parent:
            parent_rect = QtCore.QRect(
                self.parentWidget().mapToGlobal(QtCore.QPoint(0, 0)),
                self.parentWidget().size(),
            )
            self.move(
                QStyle.alignedRect(
                    QtCore.Qt.LayoutDirection.LeftToRight,
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    self.size(),
                    parent_rect,
                ).topLeft()
            )

    @staticmethod
    def line_count_distance_from_primary(current, primary, total_nr_of_lines):
        distance = primary - current
        if distance < 0:
            distance += total_nr_of_lines
        return distance

    @staticmethod
    def current_line_color(
        count_distance, total_nr_of_lines, trail_fade_perc, min_opacity, colorinput
    ):
        color = QtGui.QColor(colorinput)
        if count_distance == 0:
            return color
        min_alpha_f = min_opacity / 100.0
        distance_threshold = int(
            math.ceil((total_nr_of_lines - 1) * trail_fade_perc / 100.0)
        )
        if count_distance > distance_threshold:
            color.setAlphaF(min_alpha_f)
        else:
            alpha_diff = color.alphaF() - min_alpha_f
            gradient = alpha_diff / float(distance_threshold + 1)
            result_alpha = color.alphaF() - gradient * count_distance
            # If alpha is out of bounds, clip it.
            result_alpha = min(1.0, max(0.0, result_alpha))
            color.setAlphaF(result_alpha)
        return color
