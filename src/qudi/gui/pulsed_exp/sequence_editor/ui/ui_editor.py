# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editorwwzTfW.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from ..sequence_plot import SequencePlot
from ..creator import SequenceCreator
from ..inspector import Inspector



class Ui_SequenceEditorMainWindow(object):
    def setupUi(self, SequenceEditorMainWindow):
        if not SequenceEditorMainWindow.objectName():
            SequenceEditorMainWindow.setObjectName(u"SequenceEditorMainWindow")
        SequenceEditorMainWindow.resize(1059, 578)
        self.open_action = QAction(SequenceEditorMainWindow)
        self.open_action.setObjectName(u"open_action")
        self.save_action = QAction(SequenceEditorMainWindow)
        self.save_action.setObjectName(u"save_action")
        self.clear_action = QAction(SequenceEditorMainWindow)
        self.clear_action.setObjectName(u"clear_action")
        self.centralwidget = QWidget(SequenceEditorMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.sequence_plot = SequencePlot(self.centralwidget)
        self.sequence_plot.setObjectName(u"sequence_plot")

        self.verticalLayout.addWidget(self.sequence_plot)

        self.slider_layout = QHBoxLayout()
        self.slider_layout.setObjectName(u"slider_layout")
        self.slider_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.play_btn = QPushButton(self.centralwidget)
        self.play_btn.setObjectName(u"play_btn")
        icon = QIcon()
        iconThemeName = u"QIcon::ThemeIcon::MediaPlaybackStart"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.play_btn.setIcon(icon)
        self.play_btn.setCheckable(True)

        self.slider_layout.addWidget(self.play_btn)

        self.sim_slider = QSlider(self.centralwidget)
        self.sim_slider.setObjectName(u"sim_slider")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sim_slider.sizePolicy().hasHeightForWidth())
        self.sim_slider.setSizePolicy(sizePolicy)
        self.sim_slider.setMinimumSize(QSize(0, 0))
        self.sim_slider.setMaximumSize(QSize(16777215, 16777215))
        self.sim_slider.setMaximum(100)
        self.sim_slider.setOrientation(Qt.Horizontal)

        self.slider_layout.addWidget(self.sim_slider)

        self.iteration_lbl = QLabel(self.centralwidget)
        self.iteration_lbl.setObjectName(u"iteration_lbl")

        self.slider_layout.addWidget(self.iteration_lbl)

        self.iteration_spin = QSpinBox(self.centralwidget)
        self.iteration_spin.setObjectName(u"iteration_spin")
        self.iteration_spin.setMaximum(100)

        self.slider_layout.addWidget(self.iteration_spin)


        self.verticalLayout.addLayout(self.slider_layout)

        SequenceEditorMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(SequenceEditorMainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1059, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        SequenceEditorMainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(SequenceEditorMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        SequenceEditorMainWindow.setStatusBar(self.statusbar)
        self.sequence_creator_dock = QDockWidget(SequenceEditorMainWindow)
        self.sequence_creator_dock.setObjectName(u"sequence_creator_dock")
        self.sequence_creator = SequenceCreator()
        self.sequence_creator.setObjectName(u"sequence_creator")
        self.sequence_creator_dock.setWidget(self.sequence_creator)
        SequenceEditorMainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.sequence_creator_dock)
        self.inspector_dock = QDockWidget(SequenceEditorMainWindow)
        self.inspector_dock.setObjectName(u"inspector_dock")
        self.inspector = Inspector()
        self.inspector.setObjectName(u"inspector")
        self.inspector_dock.setWidget(self.inspector)
        SequenceEditorMainWindow.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.open_action)
        self.menuFile.addAction(self.save_action)
        self.menuFile.addAction(self.clear_action)

        self.retranslateUi(SequenceEditorMainWindow)
        self.sim_slider.valueChanged.connect(self.iteration_spin.setValue)
        self.iteration_spin.valueChanged.connect(self.sim_slider.setValue)

        QMetaObject.connectSlotsByName(SequenceEditorMainWindow)
    # setupUi

    def retranslateUi(self, SequenceEditorMainWindow):
        SequenceEditorMainWindow.setWindowTitle(QCoreApplication.translate("SequenceEditorMainWindow", u"Sequence editor", None))
        self.open_action.setText(QCoreApplication.translate("SequenceEditorMainWindow", u"Open Sequence", None))
#if QT_CONFIG(shortcut)
        self.open_action.setShortcut("")
#endif // QT_CONFIG(shortcut)
        self.save_action.setText(QCoreApplication.translate("SequenceEditorMainWindow", u"Save Sequence", None))
        self.clear_action.setText(QCoreApplication.translate("SequenceEditorMainWindow", u"Clear", None))
        self.play_btn.setText("")
        self.iteration_lbl.setText(QCoreApplication.translate("SequenceEditorMainWindow", u"Iteration", None))
        self.iteration_spin.setSuffix("")
        self.iteration_spin.setPrefix(QCoreApplication.translate("SequenceEditorMainWindow", u"i=", None))
        self.menuFile.setTitle(QCoreApplication.translate("SequenceEditorMainWindow", u"File", None))
        self.sequence_creator_dock.setWindowTitle(QCoreApplication.translate("SequenceEditorMainWindow", u"Sequence", None))
        self.inspector_dock.setWindowTitle(QCoreApplication.translate("SequenceEditorMainWindow", u"Inspector", None))
    # retranslateUi

