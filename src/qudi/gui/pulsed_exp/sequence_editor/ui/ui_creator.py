# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'creatorLsOGmy.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_CreatorWidget(object):
    def setupUi(self, CreatorWidget):
        if not CreatorWidget.objectName():
            CreatorWidget.setObjectName(u"CreatorWidget")
        CreatorWidget.resize(276, 600)
        self.verticalLayout = QVBoxLayout(CreatorWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.channel_box = QGroupBox(CreatorWidget)
        self.channel_box.setObjectName(u"channel_box")
        self.verticalLayout_3 = QVBoxLayout(self.channel_box)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.seq_name_layout = QHBoxLayout()
        self.seq_name_layout.setObjectName(u"seq_name_layout")
        self.seq_name_label = QLabel(self.channel_box)
        self.seq_name_label.setObjectName(u"seq_name_label")

        self.seq_name_layout.addWidget(self.seq_name_label)

        self.seq_name_edit = QLineEdit(self.channel_box)
        self.seq_name_edit.setObjectName(u"seq_name_edit")

        self.seq_name_layout.addWidget(self.seq_name_edit)

        self.seq_name_layout.setStretch(0, 1)
        self.seq_name_layout.setStretch(1, 2)

        self.verticalLayout_3.addLayout(self.seq_name_layout)

        self.add_channel_button = QPushButton(self.channel_box)
        self.add_channel_button.setObjectName(u"add_channel_button")

        self.verticalLayout_3.addWidget(self.add_channel_button)

        self.add_pulse_btn = QPushButton(self.channel_box)
        self.add_pulse_btn.setObjectName(u"add_pulse_btn")

        self.verticalLayout_3.addWidget(self.add_pulse_btn)

        self.iterations_layout = QHBoxLayout()
        self.iterations_layout.setObjectName(u"iterations_layout")
        self.iterations_lbl = QLabel(self.channel_box)
        self.iterations_lbl.setObjectName(u"iterations_lbl")

        self.iterations_layout.addWidget(self.iterations_lbl)

        self.iterations_spin = QSpinBox(self.channel_box)
        self.iterations_spin.setObjectName(u"iterations_spin")
        self.iterations_spin.setMaximum(999999999)

        self.iterations_layout.addWidget(self.iterations_spin)


        self.verticalLayout_3.addLayout(self.iterations_layout)

        self.io_layout = QHBoxLayout()
        self.io_layout.setObjectName(u"io_layout")
        self.save_sequence_btn = QPushButton(self.channel_box)
        self.save_sequence_btn.setObjectName(u"save_sequence_btn")

        self.io_layout.addWidget(self.save_sequence_btn)

        self.load_sequence_btn = QPushButton(self.channel_box)
        self.load_sequence_btn.setObjectName(u"load_sequence_btn")

        self.io_layout.addWidget(self.load_sequence_btn)


        self.verticalLayout_3.addLayout(self.io_layout)

        self.channels_list = QListWidget(self.channel_box)
        self.channels_list.setObjectName(u"channels_list")

        self.verticalLayout_3.addWidget(self.channels_list)


        self.verticalLayout.addWidget(self.channel_box)


        self.retranslateUi(CreatorWidget)

        QMetaObject.connectSlotsByName(CreatorWidget)
    # setupUi

    def retranslateUi(self, CreatorWidget):
        CreatorWidget.setWindowTitle(QCoreApplication.translate("CreatorWidget", u"Creator", None))
        self.channel_box.setTitle(QCoreApplication.translate("CreatorWidget", u"Sequence", None))
        self.seq_name_label.setText(QCoreApplication.translate("CreatorWidget", u"Name", None))
        self.seq_name_edit.setInputMask("")
        self.seq_name_edit.setPlaceholderText(QCoreApplication.translate("CreatorWidget", u"Insert Sequence Name", None))
        self.add_channel_button.setText(QCoreApplication.translate("CreatorWidget", u"[+] Add Channel", None))
        self.add_pulse_btn.setText(QCoreApplication.translate("CreatorWidget", u"[+] Add Pulse", None))
        self.iterations_lbl.setText(QCoreApplication.translate("CreatorWidget", u"Iterations", None))
        self.iterations_spin.setPrefix(QCoreApplication.translate("CreatorWidget", u"i=", None))
        self.save_sequence_btn.setText(QCoreApplication.translate("CreatorWidget", u"Save Sequence", None))
        self.load_sequence_btn.setText(QCoreApplication.translate("CreatorWidget", u"Load Sequence", None))
    # retranslateUi

