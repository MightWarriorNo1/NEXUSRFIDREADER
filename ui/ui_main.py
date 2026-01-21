# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QSizePolicy,
    QSpacerItem, QStackedWidget, QToolButton, QVBoxLayout,
    QWidget)
import ui.pl_rc

class Ui_Main(object):
    def setupUi(self, Main):
        if not Main.objectName():
            Main.setObjectName(u"Main")
        Main.resize(800, 560)
        self.centralwidget = QWidget(Main)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setMinimumSize(QSize(800, 540))
        self.centralwidget.setMaximumSize(QSize(16777215, 16777215))
        self.centralwidget.setStyleSheet(u"#centralwidget{\n"
"background-color: #808080;\n"
"}")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.header = QWidget(self.centralwidget)
        self.header.setObjectName(u"header")
        self.header.setMinimumSize(QSize(0, 50))
        self.header.setMaximumSize(QSize(16777215, 60))
        self.header.setStyleSheet(u"#header {\n"
"  background-color: #808080;\n"
"  border-top-right-radius: 3px;\n"
"  border-top-left-radius: 3px;\n"
"  border-bottom: 1px solid #FFFFFF;\n"
"}")
        self.horizontalLayout = QHBoxLayout(self.header)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.btn_overview = QToolButton(self.header)
        self.btn_overview.setObjectName(u"btn_overview")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_overview.sizePolicy().hasHeightForWidth())
        self.btn_overview.setSizePolicy(sizePolicy)
        self.btn_overview.setMinimumSize(QSize(130, 0))
        font = QFont()
        font.setFamilies([u"Gilroy"])
        font.setPointSize(14)
        self.btn_overview.setFont(font)
        self.btn_overview.setStyleSheet(u"color: #FFFFFF;\n"
"background-color: #595959;\n"
"border-top-right-radius: 5px;\n"
"border-top-left-radius: 5px;\n"
"padding-left: 10px;")
        icon = QIcon()
        icon.addFile(u":/img/img/home.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_overview.setIcon(icon)
        self.btn_overview.setIconSize(QSize(24, 24))
        self.btn_overview.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.horizontalLayout.addWidget(self.btn_overview)

        self.btn_settings = QToolButton(self.header)
        self.btn_settings.setObjectName(u"btn_settings")
        sizePolicy.setHeightForWidth(self.btn_settings.sizePolicy().hasHeightForWidth())
        self.btn_settings.setSizePolicy(sizePolicy)
        self.btn_settings.setMinimumSize(QSize(130, 0))
        self.btn_settings.setFont(font)
        self.btn_settings.setStyleSheet(u"color: #FFFFFF;\n"
"border: none;\n"
"border-top-right-radius: 3px;\n"
"border-top-left-radius: 3px;\n"
"background-color: #707070;\n"
"padding-left: 18px;")
        icon1 = QIcon()
        icon1.addFile(u":/img/img/gear-48.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_settings.setIcon(icon1)
        self.btn_settings.setIconSize(QSize(24, 24))
        self.btn_settings.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.horizontalLayout.addWidget(self.btn_settings)

        self.horizontalSpacer = QSpacerItem(181, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.header)

        self.stack = QStackedWidget(self.centralwidget)
        self.stack.setObjectName(u"stack")
        self.stack.setStyleSheet(u"background-color: #595959;")

        self.verticalLayout.addWidget(self.stack)

        Main.setCentralWidget(self.centralwidget)

        self.retranslateUi(Main)

        self.stack.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(Main)
    # setupUi

    def retranslateUi(self, Main):
        Main.setWindowTitle(QCoreApplication.translate("Main", u"NexusRFIDReader", None))
        self.btn_overview.setText(QCoreApplication.translate("Main", u" Overview ", None))
        self.btn_settings.setText(QCoreApplication.translate("Main", u"Settings", None))
    # retranslateUi

