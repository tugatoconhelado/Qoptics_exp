# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'inspector.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_InspectorWidget(object):
    def setupUi(self, InspectorWidget):
        if not InspectorWidget.objectName():
            InspectorWidget.setObjectName(u"InspectorWidget")
        InspectorWidget.resize(418, 759)
        self.verticalLayout = QVBoxLayout(InspectorWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.channel_box = QGroupBox(InspectorWidget)
        self.channel_box.setObjectName(u"channel_box")
        self.verticalLayout_6 = QVBoxLayout(self.channel_box)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.channel_label = QLabel(self.channel_box)
        self.channel_label.setObjectName(u"channel_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.channel_label)

        self.name_label = QLabel(self.channel_box)
        self.name_label.setObjectName(u"name_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.name_label)

        self.pb_id_combo = QComboBox(self.channel_box)
        self.pb_id_combo.setObjectName(u"pb_id_combo")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.pb_id_combo)

        self.channel_name_edit = QLineEdit(self.channel_box)
        self.channel_name_edit.setObjectName(u"channel_name_edit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.channel_name_edit)


        self.verticalLayout_6.addLayout(self.formLayout)

        self.channel_delay_box = QGroupBox(self.channel_box)
        self.channel_delay_box.setObjectName(u"channel_delay_box")
        self.formLayout_2 = QFormLayout(self.channel_delay_box)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.on_label = QLabel(self.channel_delay_box)
        self.on_label.setObjectName(u"on_label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.on_label)

        self.delay_on_spin = QSpinBox(self.channel_delay_box)
        self.delay_on_spin.setObjectName(u"delay_on_spin")
        self.delay_on_spin.setMaximum(999999999)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.delay_on_spin)

        self.off_label = QLabel(self.channel_delay_box)
        self.off_label.setObjectName(u"off_label")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.off_label)

        self.delay_off_spin = QSpinBox(self.channel_delay_box)
        self.delay_off_spin.setObjectName(u"delay_off_spin")
        self.delay_off_spin.setMaximum(999999999)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.delay_off_spin)


        self.verticalLayout_6.addWidget(self.channel_delay_box)


        self.verticalLayout.addWidget(self.channel_box)

        self.pulse_box = QGroupBox(InspectorWidget)
        self.pulse_box.setObjectName(u"pulse_box")
        self.verticalLayout_2 = QVBoxLayout(self.pulse_box)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.channel_label_2 = QLabel(self.pulse_box)
        self.channel_label_2.setObjectName(u"channel_label_2")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.channel_label_2)

        self.channel_combo = QComboBox(self.pulse_box)
        self.channel_combo.setObjectName(u"channel_combo")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.channel_combo)

        self.start_label = QLabel(self.pulse_box)
        self.start_label.setObjectName(u"start_label")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.start_label)

        self.start_spin = QSpinBox(self.pulse_box)
        self.start_spin.setObjectName(u"start_spin")
        self.start_spin.setMaximum(999999999)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.start_spin)

        self.duration_label = QLabel(self.pulse_box)
        self.duration_label.setObjectName(u"duration_label")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.duration_label)

        self.duration_spin = QSpinBox(self.pulse_box)
        self.duration_spin.setObjectName(u"duration_spin")
        self.duration_spin.setMaximum(999999999)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.duration_spin)


        self.verticalLayout_2.addLayout(self.formLayout_3)

        self.sweep_box = QGroupBox(self.pulse_box)
        self.sweep_box.setObjectName(u"sweep_box")
        self.sweep_box.setFlat(False)
        self.sweep_box.setCheckable(True)
        self.verticalLayout_3 = QVBoxLayout(self.sweep_box)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.sweep_box)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)

        self.sweep_form = QFormLayout()
        self.sweep_form.setObjectName(u"sweep_form")
        self.start_lbl = QLabel(self.sweep_box)
        self.start_lbl.setObjectName(u"start_lbl")

        self.sweep_form.setWidget(0, QFormLayout.LabelRole, self.start_lbl)

        self.sweep_start_edit = QLineEdit(self.sweep_box)
        self.sweep_start_edit.setObjectName(u"sweep_start_edit")

        self.sweep_form.setWidget(0, QFormLayout.FieldRole, self.sweep_start_edit)

        self.width_lbl = QLabel(self.sweep_box)
        self.width_lbl.setObjectName(u"width_lbl")

        self.sweep_form.setWidget(1, QFormLayout.LabelRole, self.width_lbl)

        self.sweep_duration_edit = QLineEdit(self.sweep_box)
        self.sweep_duration_edit.setObjectName(u"sweep_duration_edit")

        self.sweep_form.setWidget(1, QFormLayout.FieldRole, self.sweep_duration_edit)

        self.ripple_lbl = QLabel(self.sweep_box)
        self.ripple_lbl.setObjectName(u"ripple_lbl")

        self.sweep_form.setWidget(2, QFormLayout.LabelRole, self.ripple_lbl)

        self.ripple_combo = QComboBox(self.sweep_box)
        self.ripple_combo.addItem("")
        self.ripple_combo.addItem("")
        self.ripple_combo.addItem("")
        self.ripple_combo.setObjectName(u"ripple_combo")

        self.sweep_form.setWidget(2, QFormLayout.FieldRole, self.ripple_combo)


        self.verticalLayout_3.addLayout(self.sweep_form)


        self.verticalLayout_2.addWidget(self.sweep_box)

        self.delete_pulse_btn = QPushButton(self.pulse_box)
        self.delete_pulse_btn.setObjectName(u"delete_pulse_btn")

        self.verticalLayout_2.addWidget(self.delete_pulse_btn)


        self.verticalLayout.addWidget(self.pulse_box)


        self.retranslateUi(InspectorWidget)

        QMetaObject.connectSlotsByName(InspectorWidget)
    # setupUi

    def retranslateUi(self, InspectorWidget):
        InspectorWidget.setWindowTitle(QCoreApplication.translate("InspectorWidget", u"Form", None))
        self.channel_box.setTitle(QCoreApplication.translate("InspectorWidget", u"Channel Inspector", None))
        self.channel_label.setText(QCoreApplication.translate("InspectorWidget", u"Channel", None))
        self.name_label.setText(QCoreApplication.translate("InspectorWidget", u"Name", None))
        self.channel_delay_box.setTitle(QCoreApplication.translate("InspectorWidget", u"Delay", None))
        self.on_label.setText(QCoreApplication.translate("InspectorWidget", u"On", None))
        self.delay_on_spin.setSuffix(QCoreApplication.translate("InspectorWidget", u" ns", None))
        self.off_label.setText(QCoreApplication.translate("InspectorWidget", u"Off", None))
        self.delay_off_spin.setSuffix(QCoreApplication.translate("InspectorWidget", u" ns", None))
        self.pulse_box.setTitle(QCoreApplication.translate("InspectorWidget", u"Pulse Inspector", None))
        self.channel_label_2.setText(QCoreApplication.translate("InspectorWidget", u"Channel", None))
        self.start_label.setText(QCoreApplication.translate("InspectorWidget", u"Start", None))
        self.start_spin.setSuffix(QCoreApplication.translate("InspectorWidget", u" ns", None))
        self.duration_label.setText(QCoreApplication.translate("InspectorWidget", u"Duration", None))
        self.duration_spin.setSuffix(QCoreApplication.translate("InspectorWidget", u" ns", None))
        self.sweep_box.setTitle(QCoreApplication.translate("InspectorWidget", u"Sweep", None))
        self.label.setText(QCoreApplication.translate("InspectorWidget", u"f(S, W, i)", None))
        self.start_lbl.setText(QCoreApplication.translate("InspectorWidget", u"Start", None))
        self.sweep_start_edit.setPlaceholderText(QCoreApplication.translate("InspectorWidget", u"S + 100 * i", None))
        self.width_lbl.setText(QCoreApplication.translate("InspectorWidget", u"Width", None))
        self.sweep_duration_edit.setPlaceholderText(QCoreApplication.translate("InspectorWidget", u"W + 10 * i", None))
        self.ripple_lbl.setText(QCoreApplication.translate("InspectorWidget", u"Ripple", None))
        self.ripple_combo.setItemText(0, QCoreApplication.translate("InspectorWidget", u"none", None))
        self.ripple_combo.setItemText(1, QCoreApplication.translate("InspectorWidget", u"channel", None))
        self.ripple_combo.setItemText(2, QCoreApplication.translate("InspectorWidget", u"global", None))

        self.delete_pulse_btn.setText(QCoreApplication.translate("InspectorWidget", u"Delete Pulse", None))
    # retranslateUi

