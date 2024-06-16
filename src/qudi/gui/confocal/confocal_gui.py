# -*- coding: utf-8 -*-

import os
from PySide2.QtCore import Slot, Signal, Qt, SIGNAL

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.confocal.confocal_mainwindow import ConfocalMainWindow
import functools


class ConfocalGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _confocal_logic = Connector(name='confocal_logic', interface='ConfocalLogic')
    _tracking_logic = Connector(name='tracking_logic', interface='TrackingLogic')
    _timetrace_gui = Connector(name='timetrace_gui', interface='TimeTraceGui')
    _tcspc_gui = Connector(name='tcspc_gui', interface='TCSPCGui')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        # initialize the main window
        self._mw = ConfocalMainWindow()

        # connect all GUI internal signals

        # Signals to position control
        self._mw.scan_parameters_action.triggered.connect(
            self._mw.confocal_widget.scan_parameters_dialog.show,
            Qt.QueuedConnection
        )
        self._mw.tracking_parameters_action.triggered.connect(
            self._mw.tracking_widget.tracking_parameters_dialog.show,
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.image_fw_widget.xy_pos_signal.connect(
            self._mw.position_control_widget.on_position_indicator_moved,
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.image_bw_widget.xy_pos_signal.connect(
            self._mw.position_control_widget.on_position_indicator_moved,
            Qt.QueuedConnection
        )
        self._mw.position_control_widget.position_changed.connect(
            self._mw.confocal_widget.on_position_changed,
            Qt.QueuedConnection
        )
        self._mw.position_control_widget.position_changed.connect(
            self._tracking_logic().go_to_xy_point,
            Qt.QueuedConnection
        )
        self._mw.position_control_widget.z_changed.connect(
            self._tracking_logic().go_to_z_point,
            Qt.QueuedConnection
        )
        self._mw.position_control_widget.set_offset_signal.connect(
            self._mw.confocal_widget.scan_parameters_dialog.set_offset,
            Qt.QueuedConnection
        )

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        # Experiment control signals
        self._mw.confocal_widget.start_confocal_image_signal.connect(
            self._confocal_logic().confocal_image,
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.stop_confocal_image_signal.connect(
            self._confocal_logic().stop_acquisition,
            Qt.QueuedConnection
        )

        self._confocal_logic().progress_signal.connect(
            self._mw.update_status_bar_progress,
            Qt.QueuedConnection
        )
        self._confocal_logic().status_msg_signal.connect(
            self.update_statusbar,
            Qt.QueuedConnection
        )
        self._confocal_logic().data_signal.connect(
            self._mw.confocal_widget.update_image,
            Qt.QueuedConnection
        )
        self._confocal_logic().img_size_signal.connect(
            self._mw.confocal_widget.configure_image_axis,
            Qt.QueuedConnection
        )
        self._confocal_logic().file_changed_signal.connect(
            self.change_current_file_labels,
            Qt.QueuedConnection
        )
    
        # Data saving/loading signals
        self._mw.confocal_widget.save_button.clicked.connect(
            functools.partial(
                self._confocal_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_action.triggered.connect(
            functools.partial(
                self._confocal_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.load_button.clicked.connect(
            functools.partial(
                self._confocal_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_action.triggered.connect(
            functools.partial(
                self._confocal_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_as_action.triggered.connect(
            functools.partial(
                self._confocal_logic().save_data_as
            ),
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.previous_button.clicked.connect(
            functools.partial(
                self._confocal_logic().load_previous_data
            ),
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.next_button.clicked.connect(
            functools.partial(
                self._confocal_logic().load_next_data
            ),
            Qt.QueuedConnection
        )
        self._mw.confocal_widget.delete_button.clicked.connect(
            functools.partial(
                self._confocal_logic().delete_file
            ),
            Qt.QueuedConnection
        )

        # Connect signals related to tracking
        # Connect tracking to position control
        self._tracking_logic().max_point_signal.connect(
            self._mw.position_control_widget.set_xy_point, Qt.QueuedConnection)
        self._tracking_logic().max_z_signal.connect(
            self._mw.position_control_widget.set_z_point, Qt.QueuedConnection)

        self._mw.position_control_widget.position_changed.connect(
            self._mw.tracking_widget.xy_scan_widget.move_pos_indicator,
            Qt.QueuedConnection
        )
        
        self._mw.position_control_widget.set_z_offset_signal.connect(
            self._mw.tracking_widget.tracking_parameters_dialog.set_z_offset,
            Qt.QueuedConnection
        )
        self._mw.position_control_widget.set_offset_signal.connect(
            self._mw.tracking_widget.tracking_parameters_dialog.set_offset,
            Qt.QueuedConnection
        )

        # Connect tracking logic to gui
        self._mw.tracking_widget.maxing_signal.connect(
            self._tracking_logic().on_start_maxing, Qt.QueuedConnection)
        self._mw.tracking_widget.max_xy_signal.connect(
            self._tracking_logic().max_xy, Qt.QueuedConnection)
        self._mw.tracking_widget.max_z_signal.connect(
            self._tracking_logic().max_z, Qt.QueuedConnection)
        self._mw.tracking_widget.max_xyz_signal.connect(
            self._tracking_logic().max_xyz, Qt.QueuedConnection)
        self._mw.tracking_widget.track_signal.connect(
            self._tracking_logic().start_tracking, Qt.QueuedConnection)

        self._mw.tracking_widget.stop_button.clicked.connect(
            self._tracking_logic().stop_maxing, Qt.QueuedConnection)
        self._mw.tracking_widget.stop_button.clicked.connect(
            self._tracking_logic().stop_acquisition, Qt.QueuedConnection)

        self._tracking_logic().z_profile_signal.connect(
            self._mw.tracking_widget.plot_z_profile, Qt.QueuedConnection)
        self._tracking_logic().z_profile_fit_signal.connect(
            self._mw.tracking_widget.plot_z_fit, Qt.QueuedConnection)
        self._tracking_logic().point_profile_signal.connect(
            self._mw.tracking_widget.plot_point_profile, Qt.QueuedConnection
        )
        self._tracking_logic().point_profile_fit_signal.connect(
            self._mw.tracking_widget.plot_point_fit, Qt.QueuedConnection)
        self._tracking_logic().img_size_signal.connect(
            self._mw.tracking_widget.set_image_size, Qt.QueuedConnection)
        self._tracking_logic().img_data_signal.connect(
            self._mw.tracking_widget.update_image, Qt.QueuedConnection)
        self._tracking_logic().tracking_points_signal.connect(
            self._mw.tracking_widget.plot_tracking_points, Qt.QueuedConnection)

        self._tracking_logic().call_set_offset_signal.connect(
            self._mw.position_control_widget._on_set_offset_button_pressed, Qt.QueuedConnection)
        
        self._mw.tracking_widget.tracking_parameters_dialog.tracking_monitor_signal.connect(
            self.connect_tracking_intensity_monitor, Qt.QueuedConnection
        )
        self._mw.tracking_widget.tracking_parameters_dialog.connect_tracking_interval_signal.connect(
            self.connect_tracking_interval_to_TCSPC, Qt.QueuedConnection
        )

        self._tcspc_gui()._tcspc_logic().track_point_signal.connect(
                self._tracking_logic().track_point,
                Qt.QueuedConnection
        )
        self._timetrace_gui()._timetrace_logic().track_point_signal.connect(
            self._tracking_logic().track_point,
            Qt.QueuedConnection
        )
        self._tracking_logic().start_track_intensity_signal.connect(
            print, Qt.QueuedConnection)
        self._tracking_logic().interval_clock_signal.connect(
            self._tracking_logic().track_point,
            Qt.QueuedConnection
        )
        self._tracking_logic().tracking_finished_signal.connect(
            self._tcspc_gui()._tcspc_logic().restart_measurement,
        )
        self._tcspc_gui()._tcspc_logic().measurement_finished_signal.connect(
            self._tracking_logic().stop_maxing,
            Qt.QueuedConnection
        )
        self._tcspc_gui()._tcspc_logic().measurement_finished_signal.connect(
            self._tracking_logic().stop_acquisition,
            Qt.QueuedConnection
        )


        self.connect_tracking_intensity_monitor('TCSPC')
        
        self._mw.confocal_widget.previous_button.clicked.emit()

        self.show()

        
    def on_deactivate(self) -> None:
        self._mw.close()

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()

    @Slot(str)
    def connect_tracking_intensity_monitor(self, monitor: str) -> None:

        self._tracking_logic().start_track_intensity_signal.disconnect()

        if monitor == 'TCSPC':
            self._tracking_logic().start_track_intensity_signal.connect(
                self._tcspc_gui()._tcspc_logic().start_track_intensity,
                Qt.QueuedConnection
            )

        elif monitor == 'TimeTrace':
            self._tracking_logic().start_track_intensity_signal.connect(
                self._timetrace_gui().on_start_track_intensity,
                Qt.QueuedConnection
            )

    @Slot(bool)
    def connect_tracking_interval_to_TCSPC(self, connect: bool):

        self._tracking_logic().interval_clock_signal.disconnect()
        if connect is True:
            self._tracking_logic().interval_clock_signal.connect(
                self._tcspc_gui()._tcspc_logic().track_interval_triggered,
                Qt.QueuedConnection
            )
        elif connect is False:
            self._tracking_logic().interval_clock_signal.connect(
                self._tracking_logic().track_point,
                Qt.QueuedConnection
            )

    @Slot(str)
    def change_current_file_labels(self, filepath: str) -> None:

        head, filename = os.path.split(filepath)
        self._mw.confocal_widget.image_fw_widget.heatmap.setTitle(
            filename, **{'size': '7pt'})
        self._mw.confocal_widget.image_bw_widget.heatmap.setTitle(
            filename, **{'size': '7pt'})
        self._mw.confocal_widget.filename_label.setText(filename)

    @Slot(str, int)
    def update_statusbar(self, message: str, timeout: int = 5000) -> None:
        self._mw.statusbar.showMessage(message, timeout)