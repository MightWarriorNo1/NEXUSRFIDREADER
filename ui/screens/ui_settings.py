# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import ui.pl_rc

class Ui_SettingsScreen(object):
    def setupUi(self, SettingsScreen):
        if not SettingsScreen.objectName():
            SettingsScreen.setObjectName(u"SettingsScreen")
        SettingsScreen.resize(800, 500)
        SettingsScreen.setMinimumSize(QSize(790, 500))
        SettingsScreen.setStyleSheet(u"")
        self.verticalLayout_1 = QVBoxLayout(SettingsScreen)
        self.verticalLayout_1.setSpacing(0)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.verticalLayout_1.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_5 = QGroupBox(SettingsScreen)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.groupBox_5.setFont(font)
        self.groupBox_5.setStyleSheet(u"QGroupBox::title {  \n"
"    color: white;  /* Change 'blue' to any color you want */ \n"
"}")
        self.horizontalLayout_1 = QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_1.setObjectName(u"horizontalLayout_1")
        self.horizontalLayout_1.setContentsMargins(20, -1, 20, -1)
        self.widget_1 = QWidget(self.groupBox_5)
        self.widget_1.setObjectName(u"widget_1")
        sizePolicy.setHeightForWidth(self.widget_1.sizePolicy().hasHeightForWidth())
        self.widget_1.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(self.widget_1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget_3 = QWidget(self.widget_1)
        self.widget_3.setObjectName(u"widget_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.widget_3)
        self.verticalLayout_2.setSpacing(15)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_3 = QLabel(self.widget_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)
        self.label_3.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_2.addWidget(self.label_3)

        self.label_4 = QLabel(self.widget_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)
        self.label_4.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_2.addWidget(self.label_4)

        self.label_5 = QLabel(self.widget_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)
        self.label_5.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_2.addWidget(self.label_5)


        self.horizontalLayout_2.addWidget(self.widget_3)

        self.widget_2 = QWidget(self.widget_1)
        self.widget_2.setObjectName(u"widget_2")
        sizePolicy.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
        self.widget_2.setSizePolicy(sizePolicy)
        self.widget_2.setStyleSheet(u"QLineEdit {  \n"
"    border: 2px solid gray;  \n"
"    border-radius: 10px;  \n"
"    padding: 2 8 2 8 px;  \n"
"    background: white;  \n"
"    selection-background-color: darkgray;  \n"
"}  ")
        self.verticalLayout_3 = QVBoxLayout(self.widget_2)
        self.verticalLayout_3.setSpacing(8)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.edit_site_id = QLineEdit(self.widget_2)
        self.edit_site_id.setObjectName(u"edit_site_id")
        self.edit_site_id.setFont(font)

        self.verticalLayout_3.addWidget(self.edit_site_id)

        self.edit_record_interval_ms = QLineEdit(self.widget_2)
        self.edit_record_interval_ms.setObjectName(u"edit_record_interval_ms")
        self.edit_record_interval_ms.setFont(font)

        self.verticalLayout_3.addWidget(self.edit_record_interval_ms)

        self.edit_max_upload_records = QLineEdit(self.widget_2)
        self.edit_max_upload_records.setObjectName(u"edit_max_upload_records")
        self.edit_max_upload_records.setFont(font)

        self.verticalLayout_3.addWidget(self.edit_max_upload_records)


        self.horizontalLayout_2.addWidget(self.widget_2)


        self.horizontalLayout_1.addWidget(self.widget_1)


        self.verticalLayout.addWidget(self.groupBox_5)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_db = QGroupBox(SettingsScreen)
        self.groupBox_db.setObjectName(u"groupBox_db")
        sizePolicy.setHeightForWidth(self.groupBox_db.sizePolicy().hasHeightForWidth())
        self.groupBox_db.setSizePolicy(sizePolicy)
        self.groupBox_db.setFont(font)
        self.groupBox_db.setStyleSheet(u"QGroupBox::title {  \n"
"    color: white;  /* Change 'blue' to any color you want */ \n"
"}")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_db)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(20, -1, 20, -1)
        self.widget_db = QWidget(self.groupBox_db)
        self.widget_db.setObjectName(u"widget_db")
        sizePolicy.setHeightForWidth(self.widget_db.sizePolicy().hasHeightForWidth())
        self.widget_db.setSizePolicy(sizePolicy)
        self.horizontalLayout_4 = QHBoxLayout(self.widget_db)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.widget_10 = QWidget(self.widget_db)
        self.widget_10.setObjectName(u"widget_10")
        sizePolicy1.setHeightForWidth(self.widget_10.sizePolicy().hasHeightForWidth())
        self.widget_10.setSizePolicy(sizePolicy1)
        self.verticalLayout_5 = QVBoxLayout(self.widget_10)
        self.verticalLayout_5.setSpacing(15)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_10 = QLabel(self.widget_10)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font)
        self.label_10.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_5.addWidget(self.label_10)

        self.label_11 = QLabel(self.widget_10)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font)
        self.label_11.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_5.addWidget(self.label_11)


        self.horizontalLayout_4.addWidget(self.widget_10)

        self.widget_9 = QWidget(self.widget_db)
        self.widget_9.setObjectName(u"widget_9")
        sizePolicy.setHeightForWidth(self.widget_9.sizePolicy().hasHeightForWidth())
        self.widget_9.setSizePolicy(sizePolicy)
        self.widget_9.setStyleSheet(u"QLineEdit {  \n"
"    border: 2px solid gray;  \n"
"    border-radius: 10px;  \n"
"    padding: 2 8 2 8 px;  \n"
"    background: white;  \n"
"    selection-background-color: darkgray;  \n"
"}  ")
        self.verticalLayout_6 = QVBoxLayout(self.widget_9)
        self.verticalLayout_6.setSpacing(8)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.edit_max_records = QLineEdit(self.widget_9)
        self.edit_max_records.setObjectName(u"edit_max_records")
        self.edit_max_records.setFont(font)

        self.verticalLayout_6.addWidget(self.edit_max_records)

        self.edit_duplicate_detection_seconds = QLineEdit(self.widget_9)
        self.edit_duplicate_detection_seconds.setObjectName(u"edit_duplicate_detection_seconds")
        self.edit_duplicate_detection_seconds.setFont(font)

        self.verticalLayout_6.addWidget(self.edit_duplicate_detection_seconds)


        self.horizontalLayout_4.addWidget(self.widget_9)


        self.horizontalLayout_3.addWidget(self.widget_db)


        self.verticalLayout_4.addWidget(self.groupBox_db)

        self.groupBox_speed = QGroupBox(SettingsScreen)
        self.groupBox_speed.setObjectName(u"groupBox_speed")
        sizePolicy.setHeightForWidth(self.groupBox_speed.sizePolicy().hasHeightForWidth())
        self.groupBox_speed.setSizePolicy(sizePolicy)
        self.groupBox_speed.setFont(font)
        self.groupBox_speed.setStyleSheet(u"QGroupBox::title {  \n"
"    color: white;  /* Change 'blue' to any color you want */ \n"
"}")
        self.horizontalLayout_5 = QHBoxLayout(self.groupBox_speed)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(20, -1, 20, -1)
        self.widget_11 = QWidget(self.groupBox_speed)
        self.widget_11.setObjectName(u"widget_11")
        sizePolicy.setHeightForWidth(self.widget_11.sizePolicy().hasHeightForWidth())
        self.widget_11.setSizePolicy(sizePolicy)
        self.horizontalLayout_6 = QHBoxLayout(self.widget_11)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.widget_13 = QWidget(self.widget_11)
        self.widget_13.setObjectName(u"widget_13")
        sizePolicy1.setHeightForWidth(self.widget_13.sizePolicy().hasHeightForWidth())
        self.widget_13.setSizePolicy(sizePolicy1)
        self.verticalLayout_7 = QVBoxLayout(self.widget_13)
        self.verticalLayout_7.setSpacing(15)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_13 = QLabel(self.widget_13)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font)
        self.label_13.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_7.addWidget(self.label_13)

        self.label_14 = QLabel(self.widget_13)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font)
        self.label_14.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_7.addWidget(self.label_14)


        self.horizontalLayout_6.addWidget(self.widget_13)

        self.widget_12 = QWidget(self.widget_11)
        self.widget_12.setObjectName(u"widget_12")
        sizePolicy.setHeightForWidth(self.widget_12.sizePolicy().hasHeightForWidth())
        self.widget_12.setSizePolicy(sizePolicy)
        self.widget_12.setStyleSheet(u"QLineEdit {  \n"
"    border: 2px solid gray;  \n"
"    border-radius: 10px;  \n"
"    padding: 2 8 2 8 px;  \n"
"    background: white;  \n"
"    selection-background-color: darkgray;  \n"
"}  ")
        self.verticalLayout_8 = QVBoxLayout(self.widget_12)
        self.verticalLayout_8.setSpacing(8)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.edit_min_speed = QLineEdit(self.widget_12)
        self.edit_min_speed.setObjectName(u"edit_min_speed")
        self.edit_min_speed.setFont(font)

        self.verticalLayout_8.addWidget(self.edit_min_speed)

        self.edit_max_speed = QLineEdit(self.widget_12)
        self.edit_max_speed.setObjectName(u"edit_max_speed")
        self.edit_max_speed.setFont(font)

        self.verticalLayout_8.addWidget(self.edit_max_speed)


        self.horizontalLayout_6.addWidget(self.widget_12)


        self.horizontalLayout_5.addWidget(self.widget_11)


        self.verticalLayout_4.addWidget(self.groupBox_speed)


        self.horizontalLayout.addLayout(self.verticalLayout_4)

        self.horizontalSpacer = QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.groupBox_gps = QGroupBox(SettingsScreen)
        self.groupBox_gps.setObjectName(u"groupBox_gps")
        sizePolicy.setHeightForWidth(self.groupBox_gps.sizePolicy().hasHeightForWidth())
        self.groupBox_gps.setSizePolicy(sizePolicy)
        self.groupBox_gps.setFont(font)
        self.groupBox_gps.setStyleSheet(u"QGroupBox::title {  \n"
"    color: white;  /* Change 'blue' to any color you want */ \n"
"}")
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox_gps)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(20, -1, 20, -1)
        self.widget_gps = QWidget(self.groupBox_gps)
        self.widget_gps.setObjectName(u"widget_gps")
        sizePolicy.setHeightForWidth(self.widget_gps.sizePolicy().hasHeightForWidth())
        self.widget_gps.setSizePolicy(sizePolicy)
        self.horizontalLayout_8 = QHBoxLayout(self.widget_gps)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.widget_7 = QWidget(self.widget_gps)
        self.widget_7.setObjectName(u"widget_7")
        sizePolicy1.setHeightForWidth(self.widget_7.sizePolicy().hasHeightForWidth())
        self.widget_7.setSizePolicy(sizePolicy1)
        self.verticalLayout_10 = QVBoxLayout(self.widget_7)
        self.verticalLayout_10.setSpacing(15)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.label_8 = QLabel(self.widget_7)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font)
        self.label_8.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_10.addWidget(self.label_8)

        self.label_9 = QLabel(self.widget_7)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font)
        self.label_9.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_10.addWidget(self.label_9)


        self.horizontalLayout_8.addWidget(self.widget_7)

        self.widget_6 = QWidget(self.widget_gps)
        self.widget_6.setObjectName(u"widget_6")
        sizePolicy.setHeightForWidth(self.widget_6.sizePolicy().hasHeightForWidth())
        self.widget_6.setSizePolicy(sizePolicy)
        self.widget_6.setStyleSheet(u"QLineEdit {  \n"
"    border: 2px solid gray;  \n"
"    border-radius: 10px;  \n"
"    padding: 2 8 2 8 px;  \n"
"    background: white;  \n"
"    selection-background-color: darkgray;  \n"
"}  ")
        self.verticalLayout_11 = QVBoxLayout(self.widget_6)
        self.verticalLayout_11.setSpacing(8)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.edit_probe_baud_rate = QLineEdit(self.widget_6)
        self.edit_probe_baud_rate.setObjectName(u"edit_probe_baud_rate")
        self.edit_probe_baud_rate.setFont(font)

        self.verticalLayout_11.addWidget(self.edit_probe_baud_rate)

        self.edit_baud_rate = QLineEdit(self.widget_6)
        self.edit_baud_rate.setObjectName(u"edit_baud_rate")
        self.edit_baud_rate.setFont(font)

        self.verticalLayout_11.addWidget(self.edit_baud_rate)


        self.horizontalLayout_8.addWidget(self.widget_6)


        self.horizontalLayout_7.addWidget(self.widget_gps)


        self.verticalLayout_9.addWidget(self.groupBox_gps)

        self.groupBox_1 = QGroupBox(SettingsScreen)
        self.groupBox_1.setObjectName(u"groupBox_1")
        sizePolicy.setHeightForWidth(self.groupBox_1.sizePolicy().hasHeightForWidth())
        self.groupBox_1.setSizePolicy(sizePolicy)
        self.groupBox_1.setFont(font)
        self.groupBox_1.setStyleSheet(u"QGroupBox::title {  \n"
"    color: white;  /* Change 'blue' to any color you want */ \n"
"}")
        self.horizontalLayout_9 = QHBoxLayout(self.groupBox_1)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(20, -1, 20, -1)
        self.widget_4 = QWidget(self.groupBox_1)
        self.widget_4.setObjectName(u"widget_4")
        sizePolicy.setHeightForWidth(self.widget_4.sizePolicy().hasHeightForWidth())
        self.widget_4.setSizePolicy(sizePolicy)
        self.horizontalLayout_10 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.widget_8 = QWidget(self.widget_4)
        self.widget_8.setObjectName(u"widget_8")
        sizePolicy1.setHeightForWidth(self.widget_8.sizePolicy().hasHeightForWidth())
        self.widget_8.setSizePolicy(sizePolicy1)
        self.verticalLayout_12 = QVBoxLayout(self.widget_8)
        self.verticalLayout_12.setSpacing(15)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.label_6 = QLabel(self.widget_8)
        self.label_6.setObjectName(u"label_6")
        font1 = QFont()
        font1.setPointSize(11)
        font1.setBold(True)
        self.label_6.setFont(font1)
        self.label_6.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_12.addWidget(self.label_6)

        self.label_7 = QLabel(self.widget_8)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)
        self.label_7.setStyleSheet(u"QLabel {  \n"
"    color: white;  /* Change 'blue' to your preferred color */  \n"
"}  ")

        self.verticalLayout_12.addWidget(self.label_7)


        self.horizontalLayout_10.addWidget(self.widget_8)

        self.widget_5 = QWidget(self.widget_4)
        self.widget_5.setObjectName(u"widget_5")
        sizePolicy.setHeightForWidth(self.widget_5.sizePolicy().hasHeightForWidth())
        self.widget_5.setSizePolicy(sizePolicy)
        self.widget_5.setStyleSheet(u"QLineEdit {  \n"
"    border: 2px solid gray;  \n"
"    border-radius: 10px;  \n"
"    padding: 2 8 2 8 px;  \n"
"    background: white;  \n"
"    selection-background-color: darkgray;  \n"
"}  ")
        self.verticalLayout_13 = QVBoxLayout(self.widget_5)
        self.verticalLayout_13.setSpacing(8)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.edit_rfid_host = QLineEdit(self.widget_5)
        self.edit_rfid_host.setObjectName(u"edit_rfid_host")
        self.edit_rfid_host.setFont(font)

        self.verticalLayout_13.addWidget(self.edit_rfid_host)

        self.edit_rfid_port = QLineEdit(self.widget_5)
        self.edit_rfid_port.setObjectName(u"edit_rfid_port")
        self.edit_rfid_port.setFont(font)

        self.verticalLayout_13.addWidget(self.edit_rfid_port)


        self.horizontalLayout_10.addWidget(self.widget_5)


        self.horizontalLayout_9.addWidget(self.widget_4)


        self.verticalLayout_9.addWidget(self.groupBox_1)

        self.widget_25 = QWidget(SettingsScreen)
        self.widget_25.setObjectName(u"widget_25")
        self.verticalLayout_18 = QVBoxLayout(self.widget_25)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.setting_save_btn = QPushButton(self.widget_25)
        self.setting_save_btn.setObjectName(u"setting_save_btn")
        self.setting_save_btn.setFont(font)
        self.setting_save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setting_save_btn.setStyleSheet(u"QPushButton {\n"
"	background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,   \n"
"                                      stop:0 #222222, stop:1 #aaaaaa);\n"
"    border: 2px solid white;  \n"
"    border-radius: 10px;  \n"
"    min-width: 80px;\n"
"	min-height: 20px;\n"
"	color: white;\n"
"} \n"
"\n"
"QPushButton:hover {  \n"
"    background-color: #a0a0a0; /* Slightly different green on hover */  \n"
"}  \n"
"\n"
"QPushButton:pressed {  \n"
"    background-color: #909090; /* Darker green when pressed */  \n"
"}  ")

        self.verticalLayout_18.addWidget(self.setting_save_btn)


        self.verticalLayout_9.addWidget(self.widget_25)


        self.horizontalLayout.addLayout(self.verticalLayout_9)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_1.addLayout(self.verticalLayout)


        self.retranslateUi(SettingsScreen)

        QMetaObject.connectSlotsByName(SettingsScreen)
    # setupUi

    def retranslateUi(self, SettingsScreen):
        SettingsScreen.setWindowTitle(QCoreApplication.translate("SettingsScreen", u"Settings", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("SettingsScreen", u"API Config", None))
        self.label_3.setText(QCoreApplication.translate("SettingsScreen", u"Site ID:", None))
        self.label_4.setText(QCoreApplication.translate("SettingsScreen", u"Upload Interval Period(ms):", None))
        self.label_5.setText(QCoreApplication.translate("SettingsScreen", u"Max Upload Records:", None))
        self.edit_site_id.setText("")
        self.groupBox_db.setTitle(QCoreApplication.translate("SettingsScreen", u"Database Config", None))
        self.label_10.setText(QCoreApplication.translate("SettingsScreen", u"Max Store Records:", None))
        self.label_11.setText(QCoreApplication.translate("SettingsScreen", u"Duplicate Detection Period(s):", None))
        self.edit_max_records.setText("")
        self.edit_duplicate_detection_seconds.setText("")
        self.groupBox_speed.setTitle(QCoreApplication.translate("SettingsScreen", u"Speed Filter Config", None))
        self.label_13.setText(QCoreApplication.translate("SettingsScreen", u"Min Speed(mph):", None))
        self.label_14.setText(QCoreApplication.translate("SettingsScreen", u"Max Speed(mph):", None))
        self.edit_min_speed.setText("")
        self.edit_max_speed.setText("")
        self.groupBox_gps.setTitle(QCoreApplication.translate("SettingsScreen", u"GPS Config", None))
        self.label_8.setText(QCoreApplication.translate("SettingsScreen", u"Scan Baud Rate:", None))
        self.label_9.setText(QCoreApplication.translate("SettingsScreen", u"Read Baud Rate:", None))
        self.edit_probe_baud_rate.setText("")
        self.edit_baud_rate.setText("")
        self.groupBox_1.setTitle(QCoreApplication.translate("SettingsScreen", u"RFID Config", None))
        self.label_6.setText(QCoreApplication.translate("SettingsScreen", u"Host:", None))
        self.label_7.setText(QCoreApplication.translate("SettingsScreen", u"Port:", None))
        self.edit_rfid_host.setText("")
        self.edit_rfid_port.setText("")
        self.setting_save_btn.setText(QCoreApplication.translate("SettingsScreen", u"Save", None))
    # retranslateUi

