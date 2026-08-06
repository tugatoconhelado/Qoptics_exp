# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'control.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ControlWidget(object):
    def setupUi(self, ControlWidget):
        if not ControlWidget.objectName():
            ControlWidget.setObjectName(u"ControlWidget")
        ControlWidget.resize(614, 83)
        self.horizontalLayout = QHBoxLayout(ControlWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.slider_layout = QHBoxLayout()
        self.slider_layout.setObjectName(u"slider_layout")
        self.slider_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.play_btn = QPushButton(ControlWidget)
        self.play_btn.setObjectName(u"play_btn")
        icon = QIcon(QIcon.fromTheme(u"QIcon::ThemeIcon::MediaPlaybackStart"))
        self.play_btn.setIcon(icon)
        self.play_btn.setCheckable(True)

        self.slider_layout.addWidget(self.play_btn)

        self.sim_slider = QSlider(ControlWidget)
        self.sim_slider.setObjectName(u"sim_slider")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sim_slider.sizePolicy().hasHeightForWidth())
        self.sim_slider.setSizePolicy(sizePolicy)
        self.sim_slider.setMinimumSize(QSize(0, 0))
        self.sim_slider.setMaximumSize(QSize(16777215, 16777215))
        self.sim_slider.setMaximum(99)
        self.sim_slider.setOrientation(Qt.Orientation.Horizontal)

        self.slider_layout.addWidget(self.sim_slider, 0, Qt.AlignmentFlag.AlignVCenter)

        self.iteration_lbl = QLabel(ControlWidget)
        self.iteration_lbl.setObjectName(u"iteration_lbl")

        self.slider_layout.addWidget(self.iteration_lbl)

        self.iteration_spin = QSpinBox(ControlWidget)
        self.iteration_spin.setObjectName(u"iteration_spin")
        self.iteration_spin.setMaximum(999999999)

        self.slider_layout.addWidget(self.iteration_spin)


        self.horizontalLayout.addLayout(self.slider_layout)


        self.retranslateUi(ControlWidget)
        self.iteration_spin.valueChanged.connect(self.sim_slider.setValue)
        self.sim_slider.valueChanged.connect(self.iteration_spin.setValue)

        QMetaObject.connectSlotsByName(ControlWidget)
    # setupUi

    def retranslateUi(self, ControlWidget):
        ControlWidget.setWindowTitle(QCoreApplication.translate("ControlWidget", u"Form", None))
        self.play_btn.setText("")
        self.iteration_lbl.setText(QCoreApplication.translate("ControlWidget", u"Iteration", None))
        self.iteration_spin.setSuffix("")
        self.iteration_spin.setPrefix(QCoreApplication.translate("ControlWidget", u"i=", None))
    # retranslateUi

