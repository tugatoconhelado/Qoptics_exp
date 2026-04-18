# -*- coding: utf-8 -*-

__all__ = ['AnalizerGui']

from PySide2.QtCore import Signal, Slot, Qt
from PySide2.QtWidgets import QTableWidgetItem

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.analyzer.analyzer_mainwindow import AnalyzerMainWindow
from qudi.logic import filemanager


class AnalyzerGui(GuiBase):
    """
    This is a data analisis Gui module for qudi
    """
    
    sigAddToCounter = Signal(int)
    import_hdf5_sig = Signal(str)

    _analyzer_logic = Connector(name='analyzer_logic', interface='AnalyzerLogic')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:
        # initialize the main window
        self._mw = AnalyzerMainWindow()

        # Gui internal signals
        self._mw.refresh_button.clicked.connect(
            self._refresh_models,
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            self._select_hdf5_file,
            Qt.QueuedConnection
        )

        ### Gui Logic connections ###
        self._analyzer_logic().imported_data_sig.connect(
            self._mw.update_imported_data_tree,
            Qt.QueuedConnection
        )

        # Preview/Inspect management
        self._mw.request_inspect_info_sig.connect(
            self._analyzer_logic().fetch_inspect_info,
            Qt.QueuedConnection
        )
        self._analyzer_logic().inspect_info_sig.connect(
            self._mw.update_inspect_info,
            Qt.QueuedConnection
        )
        self._mw.request_preview_sig.connect(
            self._analyzer_logic().fetch_preview_data,
            Qt.QueuedConnection
        )
        self._analyzer_logic().preview_data_sig.connect(
            self._mw.update_preview_plot,
            Qt.QueuedConnection
        )

        # Setting axis data
        self._mw.request_data_sig.connect(
            self._analyzer_logic().fetch_data,
            Qt.QueuedConnection
        )
        self._analyzer_logic().data_sig.connect(
            self._mw.update_data_plot,
            Qt.QueuedConnection
        )

        # Managing fitting events
        self._mw.fit_button.clicked.connect(
            self._analyzer_logic().perform_fit,
            Qt.QueuedConnection
        )
        self._analyzer_logic().fit_data_sig.connect(
            self._mw.plot_fit_data,
            Qt.QueuedConnection
        )
        self._analyzer_logic().residuals_sig.connect(
            self._mw.plot_fit_residuals,
            Qt.QueuedConnection
        )
        self._analyzer_logic().fit_report_sig.connect(
            self._mw.update_fit_report,
            Qt.QueuedConnection
        )

        # Model selection and parameter setting
        self._mw.select_model_sig.connect(
            self._analyzer_logic().set_model,
            Qt.QueuedConnection
        )
        self._analyzer_logic().params_sig.connect(
            self._mw.update_parameters_table,
            Qt.QueuedConnection
        )
        self._mw.guess_button.clicked.connect(
            self._analyzer_logic().guess_parameters,
            Qt.QueuedConnection
        )
       

        # Data saving loading
        self.import_hdf5_sig.connect(
            self._analyzer_logic().import_hdf5_data,
            Qt.QueuedConnection
        )
        self._mw.save_button.clicked.connect(
            self._analyzer_logic().save_data
        )

        self.filemanager = filemanager.FileManager(
            experiment_name="analysis", exp_str="ANS")
        
        # Show the main window and raise it above all others
        self.show()

    def on_deactivate(self) -> None:
        # Close main window
        self._mw.close()

    def show(self) -> None:
        """ Mandatory method to show the main window """
        self._mw.show()
        self._mw.raise_()

    def _refresh_models(self):

        models = self._analyzer_logic().get_models()
        self._mw.models_combobox.clear()
        self._mw.models_combobox.addItems(models)

    def _select_hdf5_file(self):

        filepath = filemanager.get_load_file_path_from_dialog(file_dir=r"C:\EXP\data")
        if filepath != "":
            self.import_hdf5_sig.emit(filepath)

        