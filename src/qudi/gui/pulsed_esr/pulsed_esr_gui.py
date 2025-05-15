# -*- coding: utf-8 -*-

__all__ = ["TimeTraceGui"]

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox
from PySide2.QtCore import Slot, Qt, Signal

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.timetrace.timetrace_mainwindow import TimeTraceMainWindow
from qudi.logic import filemanager
from qudi.logic import plot
from qudi.gui.pulsed_esr.pulsed_esr_mainwindow import PulsedESRMainWindow
import functools
import pyqtgraph as pg


class PulsedESRGui(GuiBase):
    """This is a simple template GUI measurement module for qudi"""

    add_channel_to_logic_signal = Signal(int, list, str, int)
    prepare_frame_signal = Signal(int)
    add_pulse_to_logic_signal = Signal(float, float, str, str, list, int)
    run_exp_to_logic_signal = Signal(int, int)
    stop_exp_to_logic_signal = Signal()
    frame_to_logic_signal = Signal(int)
    simulation_to_logic = Signal(int, int, int)
    clear_logic_to_signal = Signal()

    _pulsed_esr_logic = Connector(name="pulsed_esr_logic", interface="PulsedESRLogic")

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self._mw = PulsedESRMainWindow()  # initializes the UI form

        ########## SIGNALS and connectios ##########

        ##### ADDING CHANNELS #####
        # from gui window to gui slots
        self._mw.add_channel_button.clicked.connect(self.add_channel_gui)
        self._pulsed_esr_logic().adding_flag_to_list.connect(self.update_list_channels)
        # from gui slots to logic
        self.add_channel_to_logic_signal.connect(self._pulsed_esr_logic().add_channel)

        ######## Adding and varying pulses ##############
        # from gui window to gui slots
        self._pulsed_esr_logic().error_str_signal.connect(self.show_error_message)
        self._mw.add_pulse_button.clicked.connect(self.add_pulse_gui)
        self._mw.iteration_start_spinbox.valueChanged.connect(self.set_max)
        # from gui slots to logic
        self.add_pulse_to_logic_signal.connect(
            self._pulsed_esr_logic().add_pulse_to_channel
        )

        ######## Selecting Frame for Display #######
        # from gui window to gui slots
        self._mw.iteration_frame_spinbox.setMinimum(1)
        self._mw.iteration_frame_spinbox.valueChanged.connect(self.prepare_frame)
        self._mw.update_button.clicked.connect(self.prepare_frame)
        # from gui slots to logic
        self.frame_to_logic_signal.connect(self._pulsed_esr_logic().prepare_frame)
        self._pulsed_esr_logic().frame_data_signal.connect(
            self._mw.create_frame
        ) 

        ####### Run Simulation ########
        # from gui window to gui slots
        self._mw.stop_simulation_button.clicked.connect(self.start_simulation)
        self._pulsed_esr_logic().next_frame_signal.connect(
            self.prepare_next_frame_simulation
        )
        self._pulsed_esr_logic().add_iteration_txt.connect(self.add_iteration_text)
        # from gui slots to logic
        self.frame_to_logic_signal.connect(self._pulsed_esr_logic().prepare_frame)
        self.simulation_to_logic.connect(self._pulsed_esr_logic().Run_Simulation)

        ####### RUn Experiment #######
        # from gui window to gui slots
        self._mw.run_sequence_button.clicked.connect(self.run_experiment_gui)
        self._mw.stop_sequence_button.clicked.connect(self.stop_experiment_gui)
        # from gui slots to logic
        self.run_exp_to_logic_signal.connect(self._pulsed_esr_logic().Run_experiment)
        self.stop_exp_to_logic_signal.connect(self._pulsed_esr_logic().Stop_Experiment)

        ###### Clear Gui #######
        # from gui window to gui slots
        self._mw.clear_channels_button.clicked.connect(self.clear_gui)

        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        # self._template_logic().sigCounterupdate_buttond.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    def add_channel_gui(self):
        """
        This function is called when the user clicks the "Add Channel" button.
        It checks if the channel is valid and adds it to the list.
        """
        channel_tag = self._mw.channel_identifier_combobox.currentIndex()
        print(f"channel added:{channel_tag}")
        delay = [self._mw.delay_on_spinbox.value(), self._mw.delay_off_spinbox.value()]
        channel_label = (
            self._mw.channel_type_line_edit.text()
        )  # we get the label of the channel from the gui
        channel_label = channel_label.lower()  # we leave it undercase
        channel_count = self._mw.channel_identifier_combobox.count()
        # self._pulsed_esr_logic().add_channel(channel_tag,delay,channel_label,channel_count)
        self.add_channel_to_logic_signal.emit(
            channel_tag, delay, channel_label, channel_count
        )

    @Slot(str)
    def update_list_channels(self, flag_str):
        """
        This function is called when a channel is added to the list.
        It updates the list of channels in the GUI.
        """
        # print(f"Adding channel: {flag_str}")
        self._mw.channel_list_listwidget.addItem(flag_str)

    def add_pulse_gui(self):
        """
        This function is called when the user clicks the "Add Pulse" button.
        It checks if the pulse is valid and adds it to the list.
        """
        start_time = self._mw.start_time_spinbox.value()
        width = self._mw.pulse_width_spinbox.value()
        channel_tag = (
            self._mw.pulse_channel_combobox.currentIndex()
        )  # we get the channel from the gui
        function_width = (
            self._mw.width_function_line_edit.text()
        )  # we get the function from the gui
        function_start = self._mw.start_function_line_edit.text()
        iteration_range = [
            self._mw.iteration_start_spinbox.value(),
            self._mw.iteration_end_spinbox.value(),
        ]
        # self._pulsed_esr_logic().add_pulse_to_channel(start_time, width,function_width,function_start,iteration_range, channel_tag)
        self.add_pulse_to_logic_signal.emit(
            start_time,
            width,
            function_width,
            function_start,
            iteration_range,
            channel_tag,
        )

    def set_max(self):
        self._mw.iteration_end_spinbox.setMinimum(
            self._mw.iteration_start_spinbox.value() + 1
        )

    def run_experiment_gui(self):
        value_loop = self._mw.loop_sequence_spinbox.value()
        Type = self._mw.type_variation_combobox.currentIndex()
        # self._pulsed_esr_logic().Run_experiment(value_loop,Type)
        self.run_exp_to_logic_signal.emit(value_loop, Type)

    def stop_experiment_gui(self):
        # self._pulsed_esr_logic().Stop_Experiment()
        self.stop_exp_to_logic_signal.emit()

    def prepare_frame(self):
        Frame_i = self._mw.iteration_frame_spinbox.value()
        self._mw.sequence_diagram_plot.clear()
        self._mw.sequence_diagram_plot.enableAutoRange(
            axis=pg.ViewBox.XAxis, enable=False
        )
        self._mw.sequence_diagram_plot.setXRange(
            0, self._pulsed_esr_logic().Max_end_time, padding=0
        )  # or whatever fixed length you want
        self.frame_to_logic_signal.emit(Frame_i)


    def start_simulation(self):
        initial_frame = self._mw.iteration_frame_spinbox.value()
        print(f"initial frame:{initial_frame}")
        ms = self._mw.ms.value()
        print(f"ms:{ms}")
        value_loop = self._mw.loop_sequence_spinbox.value()
        print(f"value_loop: {value_loop}")
        # self._pulsed_esr_logic().Run_Simulation(initial_frame,value_loop,ms)
        self.simulation_to_logic.emit(initial_frame, value_loop, ms)
        # Disable the button after click

    def prepare_next_frame_simulation(self, Frame_i):
        self._mw.sequence_diagram_plot.clear()
        self._mw.sequence_diagram_plot.enableAutoRange(
            axis=pg.ViewBox.XAxis, enable=False
        )
        self._mw.sequence_diagram_plot.setXRange(
            0, self._pulsed_esr_logic().Max_end_time, padding=0
        )  # or whatever fixed length you want
        # self._pulsed_esr_logic().prepare_frame(Frame_i) #this prepares the
        self.frame_to_logic_signal.emit(Frame_i)

    def add_iteration_text(self, text):
        self._mw.current_iteration.setText(text)

    def clear_gui(self):
        self._mw.channel_list_listwidget.clear()
        self._mw.sequence_diagram_plot.clear()
        self._mw.Duration_Loop.setText("Duration: ( )")
        self._mw.current_iteration.setText("current iteration: ( )")
        # self._pulsed_esr_logic().Clearing_Gui()
        self.clear_logic_to_signal.emit()

    @Slot(str)
    def show_error_message(self, error_str):
        """
        This function is called when an error occurs.
        It shows an error message to the user.
        """
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Error!")
        dlg.setText(error_str)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def show(self) -> None:
        """Show the main window and raise it above all others"""
        self._mw.show()
        self._mw.raise_()
