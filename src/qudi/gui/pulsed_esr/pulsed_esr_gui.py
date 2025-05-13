# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox
from PySide2.QtCore import Slot, Qt

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
    """ This is a simple template GUI measurement module for qudi """
    
    _pulsed_esr_logic = Connector(name='pulsed_esr_logic', interface='PulsedESRLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        #print("Initializing UI...")
        self._mw = PulsedESRMainWindow() # initializes the UI form

        self._mw.run_sequence_button.clicked.connect(self.Run_Experiment_Gui)
        self._mw.stop_sequence_button.clicked.connect(self.Stop_Experiment_Gui)

        ########## SIGNALS and connectios ##########
        
          ##### ADDING CHANNELS #####
        self._mw.add_channel_button.clicked.connect(self.add_channel_gui)
        self._pulsed_esr_logic().adding_flag_to_list.connect(self.update_list_channels)
         
        ######## Adding and varying pulses ##############
        self._pulsed_esr_logic().error_str_signal.connect(self.show_error_message)
        self._mw.add_pulse_button.clicked.connect(self.add_pulse_gui)
        self._mw.iteration_start_spinbox.valueChanged.connect(self.set_max)

        ######## Selecting Frame for Display #######
        self._mw.iteration_frame_spinbox.valueChanged.connect(self.Prepare_Frame)
        self._mw.update_button.clicked.connect(self.Prepare_Frame)
        self._pulsed_esr_logic().add_frame_to_graph.connect(self.Show_Frame)

        ####### Run Simulation ########
        self._mw.stop_simulation_button.clicked.connect(self.Start_Simulation)
        self._pulsed_esr_logic().next_frame_signal.connect(self.Prepare_next_Frame_Simulation)
        self._pulsed_esr_logic().add_iteration_txt.connect(self.add_iteration_text)
        ###### Clear Gui #######
        self._mw.clear_channels_button.clicked.connect(self.Clear_Gui())
        ##### ADDING CHANNELS #####

        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    def add_channel_gui(self):
        """
        This function is called when the user clicks the "Add Channel" button.
        It checks if the channel is valid and adds it to the list.
        """
        channel_tag = self._mw.Channel_Identifier.currentIndex()
        print(f"channel added:{channel_tag}")
        delay= [self._mw.Delay_ON.value(),self._mw.Delay_OFF.value()]
        channel_label = self._mw.Type_Channel.text()#we get the label of the channel from the gui
        channel_label=channel_label.lower() #we leave it undercase
        channel_count=self._mw.Channel_Identifier.count()
        self._pulsed_esr_logic().add_channel(channel_tag,delay,channel_label,channel_count)



    @Slot(str) #The @Slot decorator in PySide2 is used to explicitly define a method as a slot, which can be connected to a signal. It improves performance and type safety by specifying the expected argument types.
    def update_list_channels(self, flag_str):
        """
        This function is called when a channel is added to the list.
        It updates the list of channels in the GUI.
        """
        #print(f"Adding channel: {flag_str}")
        self._mw.channel_list_listwidget.addItem(flag_str)


    ##### ADDING PULSES ######
    def add_pulse_gui(self):
        """
        This function is called when the user clicks the "Add Pulse" button.
        It checks if the pulse is valid and adds it to the list.
        """
        start_time = self._mw.StartTime.value()
        width = self._mw.Puls_Width.value()
        channel_tag = self._mw.Channel_Pulse.currentIndex() #we get the channel from the gui
        function_width=self._mw.Function_Width.text() #we get the function from the gui
        function_start=self._mw.Function_Start.text()
        iteration_range = [self._mw.Iterations_start.value(),self._mw.Iterations_end.value()]
        self._pulsed_esr_logic().add_pulse_to_channel(start_time, width,function_width,function_start,iteration_range, channel_tag)

    def set_max(self): # as soon as I change the value fo the Iteration_start, the Iteration _end, allow numbers bigger than the Iterations_start
        self._mw.Iterations_end.setMinimum(self._mw.Iterations_start.value()+1) 



    #### RUN Experiment ####
    def Run_Experiment_Gui(self):
        value_loop=self._mw.Loop_Sequence.value()
        self._pulsed_esr_logic().Run_experiment(value_loop)
    def Stop_Experiment_Gui(self):
        self._pulsed_esr_logic().Stop_Experiment()

     ######## Selecting Frame for Display #######
    def Prepare_Frame(self):
        Frame_i=self._mw.Iteration_frame.value()
        self._mw.sequence_diagram_plot.clear()
        self._mw.sequence_diagram_plot.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self._mw.sequence_diagram_plot.setXRange(0, self._pulsed_esr_logic().Max_end_time, padding=0)  # or whatever fixed length you want
        self._pulsed_esr_logic().Prepare_Frame(Frame_i) #this prepares the 
        #we set the value of the x axis to the largest end time of all the iterations from all the channel

    def Show_Frame(self,sequence):
        self._mw.sequence_diagram_plot.addItem(sequence)

    ####### Simulation #######
    def Start_Simulation(self):
        initial_frame=self._mw.Iteration_frame.value()
        print(f"initial frame:{initial_frame}")
        ms=self._mw.ms.value()
        print(f"ms:{ms}")
        value_loop=self._mw.Loop_Sequence.value()
        print(f"value_loop: {value_loop}")
        self._pulsed_esr_logic().Run_Simulation(initial_frame,value_loop,ms)
        # Disable the button after click
    def Prepare_next_Frame_Simulation(self,Frame_i):
        self._mw.sequence_diagram_plot.clear()
        self._mw.sequence_diagram_plot.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self._mw.sequence_diagram_plot.setXRange(0, self._pulsed_esr_logic().Max_end_time, padding=0)  # or whatever fixed length you want
        self._pulsed_esr_logic().Prepare_Frame(Frame_i) #this prepares the 
    def add_iteration_text(self,text):
        self._mw.current_iteration_label.setText(text)
    
    ###### CLearing Gui ######
    def Clear_Gui(self):
        self._mw.channel_list_listwidget.clear()
        self._mw.sequence_diagram_plot.clear()
        self._mw.loop_duration_label.setText("Duration: ( )")
        self._mw.current_iteration_label.setText("current iteration: ( )")
        self._pulsed_esr_logic().Clearing_Gui()
        
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
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
