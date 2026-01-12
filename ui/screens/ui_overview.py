# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'overview.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)
import ui.pl_rc

class Ui_OverviewScreen(object):
    def setupUi(self, OverviewScreen):
        if not OverviewScreen.objectName():
            OverviewScreen.setObjectName(u"OverviewScreen")
        OverviewScreen.resize(800, 500)
        OverviewScreen.setMinimumSize(QSize(790, 500))
        OverviewScreen.setStyleSheet(u"")
        self.verticalLayout_20 = QVBoxLayout(OverviewScreen)
        self.verticalLayout_20.setSpacing(0)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_24 = QLabel(OverviewScreen)
        self.label_24.setObjectName(u"label_24")
        font = QFont()
        font.setFamilies([u"Gilroy"])
        font.setPointSize(14)
        font.setBold(True)
        self.label_24.setFont(font)
        self.label_24.setStyleSheet(u"color: #ffffff;")
        self.label_24.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.label_24)

        self.device_id = QLabel(OverviewScreen)
        self.device_id.setObjectName(u"device_id")
        font1 = QFont()
        font1.setFamilies([u"Gilroy"])
        font1.setPointSize(14)
        font1.setBold(False)
        self.device_id.setFont(font1)
        self.device_id.setStyleSheet(u"color: #ffffff;")
        self.device_id.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.device_id)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_4 = QWidget(OverviewScreen)
        self.widget_4.setObjectName(u"widget_4")
        self.widget_4.setStyleSheet(u"#widget_4{\n"
"	border: 2px solid #404040;\n"
"    border-right: 0px;\n"
"    border-left: 0px;\n"
"}")
        self.verticalLayout_1 = QVBoxLayout(self.widget_4)
        self.verticalLayout_1.setSpacing(2)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.verticalLayout_1.setContentsMargins(0, 4, 0, 4)
        self.label = QLabel(self.widget_4)
        self.label.setObjectName(u"label")
        font2 = QFont()
        font2.setFamilies([u"Gilroy"])
        font2.setPointSize(12)
        font2.setBold(True)
        self.label.setFont(font2)
        self.label.setStyleSheet(u"color: #ffffff;\n"
"border-bottom: 2px solid #404040;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_1.addWidget(self.label)

        self.widget_1 = QWidget(self.widget_4)
        self.widget_1.setObjectName(u"widget_1")
        self.widget_1.setStyleSheet(u"")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_1)
        self.horizontalLayout_5.setSpacing(4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.widget_1)
        self.label_3.setObjectName(u"label_3")
        font3 = QFont()
        font3.setFamilies([u"Gilroy"])
        font3.setPointSize(10)
        font3.setBold(True)
        self.label_3.setFont(font3)
        self.label_3.setStyleSheet(u"color: #ffffff;")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_3)

        self.rfid_connection_status = QLabel(self.widget_1)
        self.rfid_connection_status.setObjectName(u"rfid_connection_status")
        font4 = QFont()
        font4.setFamilies([u"Gilroy"])
        font4.setPointSize(9)
        self.rfid_connection_status.setFont(font4)
        self.rfid_connection_status.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_5.addWidget(self.rfid_connection_status)


        self.verticalLayout_1.addWidget(self.widget_1)

        self.widget_2 = QWidget(self.widget_4)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setStyleSheet(u"")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_4.setSpacing(4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.widget_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font3)
        self.label_5.setStyleSheet(u"color: #ffffff;")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.label_5)

        self.last_rfid_read = QLabel(self.widget_2)
        self.last_rfid_read.setObjectName(u"last_rfid_read")
        self.last_rfid_read.setFont(font4)
        self.last_rfid_read.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_4.addWidget(self.last_rfid_read)


        self.verticalLayout_1.addWidget(self.widget_2)

        self.widget_3 = QWidget(self.widget_4)
        self.widget_3.setObjectName(u"widget_3")
        self.widget_3.setStyleSheet(u"")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.widget_3)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font3)
        self.label_7.setStyleSheet(u"color: #ffffff;")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_7)

        self.last_rfid_time = QLabel(self.widget_3)
        self.last_rfid_time.setObjectName(u"last_rfid_time")
        self.last_rfid_time.setFont(font4)
        self.last_rfid_time.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_3.addWidget(self.last_rfid_time)


        self.verticalLayout_1.addWidget(self.widget_3)


        self.horizontalLayout.addWidget(self.widget_4)

        self.vDivider = QFrame(OverviewScreen)
        self.vDivider.setObjectName(u"vDivider")
        self.vDivider.setMinimumSize(QSize(2, 0))
        self.vDivider.setMaximumSize(QSize(2, 16777215))
        self.vDivider.setStyleSheet(u"QFrame#vDivider { background-color: #404040; }")
        self.vDivider.setFrameShape(QFrame.Shape.NoFrame)

        self.horizontalLayout.addWidget(self.vDivider)

        self.widget_5 = QWidget(OverviewScreen)
        self.widget_5.setObjectName(u"widget_5")
        self.widget_5.setStyleSheet(u"#widget_5{\n"
"	border: 2px solid #404040;\n"
"    border-left: 0px;\n"
"    border-right: 0px;\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(self.widget_5)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 4, 0, 4)
        self.label_2 = QLabel(self.widget_5)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)
        self.label_2.setStyleSheet(u"color: #ffffff;\n"
"border-bottom: 2px solid #404040;")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_2)

        self.widget_6 = QWidget(self.widget_5)
        self.widget_6.setObjectName(u"widget_6")
        self.horizontalLayout_8 = QHBoxLayout(self.widget_6)
        self.horizontalLayout_8.setSpacing(4)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_9 = QLabel(self.widget_6)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font3)
        self.label_9.setStyleSheet(u"color: #ffffff;")
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_9)

        self.gps_connection_status = QLabel(self.widget_6)
        self.gps_connection_status.setObjectName(u"gps_connection_status")
        self.gps_connection_status.setFont(font4)
        self.gps_connection_status.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_8.addWidget(self.gps_connection_status)


        self.verticalLayout_3.addWidget(self.widget_6)

        self.widget_7 = QWidget(self.widget_5)
        self.widget_7.setObjectName(u"widget_7")
        self.horizontalLayout_7 = QHBoxLayout(self.widget_7)
        self.horizontalLayout_7.setSpacing(4)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_11 = QLabel(self.widget_7)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font3)
        self.label_11.setStyleSheet(u"color: #ffffff;")
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.label_11)

        self.last_gps_read = QLabel(self.widget_7)
        self.last_gps_read.setObjectName(u"last_gps_read")
        self.last_gps_read.setFont(font4)
        self.last_gps_read.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_7.addWidget(self.last_gps_read)


        self.verticalLayout_3.addWidget(self.widget_7)

        self.widget_8 = QWidget(self.widget_5)
        self.widget_8.setObjectName(u"widget_8")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_8)
        self.horizontalLayout_6.setSpacing(4)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_13 = QLabel(self.widget_8)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font3)
        self.label_13.setStyleSheet(u"color: #ffffff;")
        self.label_13.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_13)

        self.last_gps_time = QLabel(self.widget_8)
        self.last_gps_time.setObjectName(u"last_gps_time")
        self.last_gps_time.setFont(font4)
        self.last_gps_time.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_6.addWidget(self.last_gps_time)


        self.verticalLayout_3.addWidget(self.widget_8)


        self.horizontalLayout.addWidget(self.widget_5)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget = QTableWidget(OverviewScreen)
        if (self.tableWidget.columnCount() < 7):
            self.tableWidget.setColumnCount(7)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        if (self.tableWidget.rowCount() < 8):
            self.tableWidget.setRowCount(8)
        self.tableWidget.setObjectName(u"tableWidget")
        font5 = QFont()
        font5.setPointSize(7)
        self.tableWidget.setFont(font5)
        self.tableWidget.setStyleSheet(u"\n"
"        QHeaderView::section {  \n"
"            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,   \n"
"                                            stop:0 #777777, stop:1 #000000);\n"
"            color: white;  \n"
"            padding: 3px;\n"
"            font: 14px bold;\n"
"            border: 1px solid #555;  \n"
"        }  \n"
"        QTableWidget::item {\n"
"            background-color: rgba(40, 40, 40, 150);  \n"
"            color: white;\n"
"            border: 1px solid #202020;\n"
"            padding: 3px  \n"
"        }  \n"
"        /*QTableWidget::item:selected {  \n"
"            background-color: #336699;  \n"
"            \n"
"        } */")
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setRowCount(8)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(True)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(30)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(50)
        self.tableWidget.horizontalHeader().setHighlightSections(True)
        self.tableWidget.horizontalHeader().setProperty(u"showSortIndicator", False)
        self.tableWidget.horizontalHeader().setStretchLastSection(False)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setHighlightSections(True)

        self.verticalLayout.addWidget(self.tableWidget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 4, 0, 4)
        self.widget_9 = QWidget(OverviewScreen)
        self.widget_9.setObjectName(u"widget_9")
        self.widget_9.setStyleSheet(u"#widget_9{\n"
"	border: 2px solid #404040;\n"
"    border-right: 0px;\n"
"    border-left: 0px;\n"
"}")
        self.verticalLayout_4 = QVBoxLayout(self.widget_9)
        self.verticalLayout_4.setSpacing(2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 4, 0, 4)
        self.label_15 = QLabel(self.widget_9)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setFont(font2)
        self.label_15.setStyleSheet(u"color: #ffffff;")
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.label_15)

        self.widget_10 = QWidget(self.widget_9)
        self.widget_10.setObjectName(u"widget_10")
        self.horizontalLayout_10 = QHBoxLayout(self.widget_10)
        self.horizontalLayout_10.setSpacing(4)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_16 = QLabel(self.widget_10)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setFont(font3)
        self.label_16.setStyleSheet(u"color: #ffffff;")
        self.label_16.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_10.addWidget(self.label_16)

        self.truck_number = QLabel(self.widget_10)
        self.truck_number.setObjectName(u"truck_number")
        self.truck_number.setFont(font4)
        self.truck_number.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_10.addWidget(self.truck_number)


        self.verticalLayout_4.addWidget(self.widget_10)

        self.widget_11 = QWidget(self.widget_9)
        self.widget_11.setObjectName(u"widget_11")
        self.horizontalLayout_11 = QHBoxLayout(self.widget_11)
        self.horizontalLayout_11.setSpacing(4)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_17 = QLabel(self.widget_11)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setFont(font3)
        self.label_17.setStyleSheet(u"color: #ffffff;")
        self.label_17.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_11.addWidget(self.label_17)

        self.site_id = QLabel(self.widget_11)
        self.site_id.setObjectName(u"site_id")
        self.site_id.setFont(font4)
        self.site_id.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_11.addWidget(self.site_id)


        self.verticalLayout_4.addWidget(self.widget_11)


        self.horizontalLayout_2.addWidget(self.widget_9)

        self.vDivider2 = QFrame(OverviewScreen)
        self.vDivider2.setObjectName(u"vDivider2")
        self.vDivider2.setMinimumSize(QSize(2, 0))
        self.vDivider2.setMaximumSize(QSize(2, 16777215))
        self.vDivider2.setStyleSheet(u"QFrame#vDivider2 { background-color: #404040; }")
        self.vDivider2.setFrameShape(QFrame.Shape.NoFrame)

        self.horizontalLayout_2.addWidget(self.vDivider2)

        self.widget_12 = QWidget(OverviewScreen)
        self.widget_12.setObjectName(u"widget_12")
        self.widget_12.setStyleSheet(u"#widget_12{\n"
"	border: 2px solid #404040;\n"
"    border-right: 0px;\n"
"    border-left: 0px;\n"
"}")
        self.verticalLayout_5 = QVBoxLayout(self.widget_12)
        self.verticalLayout_5.setSpacing(2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 4, 0, 4)
        self.label_20 = QLabel(self.widget_12)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setFont(font2)
        self.label_20.setStyleSheet(u"color: #ffffff;")
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.label_20)

        self.widget_14 = QWidget(self.widget_12)
        self.widget_14.setObjectName(u"widget_14")
        self.horizontalLayout_12 = QHBoxLayout(self.widget_14)
        self.horizontalLayout_12.setSpacing(4)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.label_21 = QLabel(self.widget_14)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setFont(font3)
        self.label_21.setStyleSheet(u"color: #ffffff;")
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_12.addWidget(self.label_21)

        self.internet_status = QLabel(self.widget_14)
        self.internet_status.setObjectName(u"internet_status")
        self.internet_status.setFont(font4)
        self.internet_status.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_12.addWidget(self.internet_status)


        self.verticalLayout_5.addWidget(self.widget_14)

        self.widget_15 = QWidget(self.widget_12)
        self.widget_15.setObjectName(u"widget_15")
        self.horizontalLayout_14 = QHBoxLayout(self.widget_15)
        self.horizontalLayout_14.setSpacing(4)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.label_22 = QLabel(self.widget_15)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setFont(font3)
        self.label_22.setStyleSheet(u"color: #ffffff;")
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.label_22)

        self.internet_tunnel = QLabel(self.widget_15)
        self.internet_tunnel.setObjectName(u"internet_tunnel")
        self.internet_tunnel.setFont(font4)
        self.internet_tunnel.setStyleSheet(u"color: #ffffff;")

        self.horizontalLayout_14.addWidget(self.internet_tunnel)


        self.verticalLayout_5.addWidget(self.widget_15)


        self.horizontalLayout_2.addWidget(self.widget_12)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.verticalLayout_20.addLayout(self.verticalLayout)


        self.retranslateUi(OverviewScreen)

        QMetaObject.connectSlotsByName(OverviewScreen)
    # setupUi

    def retranslateUi(self, OverviewScreen):
        OverviewScreen.setWindowTitle(QCoreApplication.translate("OverviewScreen", u"Overview", None))
        self.label_24.setText(QCoreApplication.translate("OverviewScreen", u"Device ID:", None))
        self.device_id.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label.setText(QCoreApplication.translate("OverviewScreen", u"RFID Health Status", None))
        self.label_3.setText(QCoreApplication.translate("OverviewScreen", u"RFID Connection Status: ", None))
        self.rfid_connection_status.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_5.setText(QCoreApplication.translate("OverviewScreen", u"Last RFID Tag Read: ", None))
        self.last_rfid_read.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_7.setText(QCoreApplication.translate("OverviewScreen", u"Last RFID Read Time: ", None))
        self.last_rfid_time.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_2.setText(QCoreApplication.translate("OverviewScreen", u"GPS Health Status", None))
        self.label_9.setText(QCoreApplication.translate("OverviewScreen", u"GPS Connection Status: ", None))
        self.gps_connection_status.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_11.setText(QCoreApplication.translate("OverviewScreen", u"Last GPS Read: ", None))
        self.last_gps_read.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_13.setText(QCoreApplication.translate("OverviewScreen", u"Last GPS Read Time: ", None))
        self.last_gps_time.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("OverviewScreen", u"Time", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("OverviewScreen", u"Tag", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("OverviewScreen", u"Antenna", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("OverviewScreen", u"RSSI", None));
        ___qtablewidgetitem4 = self.tableWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("OverviewScreen", u"Position", None));
        ___qtablewidgetitem5 = self.tableWidget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("OverviewScreen", u"Speed", None));
        ___qtablewidgetitem6 = self.tableWidget.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("OverviewScreen", u"Heading", None));
        self.label_15.setText(QCoreApplication.translate("OverviewScreen", u"Site Details", None))
        self.label_16.setText(QCoreApplication.translate("OverviewScreen", u"Truck Number: ", None))
        self.truck_number.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_17.setText(QCoreApplication.translate("OverviewScreen", u"Site ID: ", None))
        self.site_id.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_20.setText(QCoreApplication.translate("OverviewScreen", u"Network Health", None))
        self.label_21.setText(QCoreApplication.translate("OverviewScreen", u"Internet Status: ", None))
        self.internet_status.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
        self.label_22.setText(QCoreApplication.translate("OverviewScreen", u"Current Connection", None))
        self.internet_tunnel.setText(QCoreApplication.translate("OverviewScreen", u"N/A", None))
    # retranslateUi

