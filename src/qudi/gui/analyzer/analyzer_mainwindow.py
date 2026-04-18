from PySide2.QtWidgets import QButtonGroup,QLabel, QMainWindow, QHBoxLayout, QApplication, QTableWidgetItem, QFileDialog, QTreeWidgetItem
from PySide2.QtCore import Slot, Signal, QDir, QObject, Qt, QRectF
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os
engine_path = r'C:\EXP\python\lab_analyzer'
if engine_path not in sys.path:
    sys.path.append(engine_path)

from analysis_engine import InspectInfo, DataResult


class AnalyzerMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    request_preview_sig = Signal(str)
    request_data_sig = Signal(str, str)
    request_inspect_info_sig = Signal(str)
    select_model_sig = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.join(os.path.dirname(__file__), "analyzer.ui"), self)

        self.preview_index = 2
        self.axis_options_path = {}

        self.imported_data_tree.currentItemChanged.connect(
            self._on_tree_selection_changed)
        self.x_axis_combobox.currentTextChanged.connect(self._select_axis_data)
        self.y_axis_combobox.currentTextChanged.connect(self._select_axis_data)
        self.models_combobox.currentTextChanged.connect(
            self._select_model,
            Qt.QueuedConnection
        )
        self.configure_plots()

        self.toggleGroup = QButtonGroup(self)
        self.toggleGroup.addButton(self.display_button, 0) # ID 0
        self.toggleGroup.addButton(self.inspect_button, 1) # ID 1
        self.toggleGroup.setExclusive(True) # Only one can be pressed

        # Set the default state (Preview active)
        self.inspect_button.setChecked(True)

        self.toggleGroup.buttonClicked.connect(self._on_toggle_clicked)
        self._apply_segmented_style()

    def _apply_segmented_style(self):
        # We apply this CSS to the PARENT frame (toggle_frame). 
        # The buttons will inherit the base styles.
        # This CSS is slightly modernized for a pro look on Windows 7.
        qss = """
            /* Apply to toggle_frame */
            QFrame#toggle_frame {
                background-color: #000000; 
                border-radius: 0px;
                padding: 0px;
                border: 1px solid transparent;
            }

            QFrame#toggle_frame QPushButton {
                margin: 0px;
                border: 1px solid #8f14f5;
                padding: 6px 6px;
                color: #fff;
                background-color: black;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton#display_button {
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QPushButton#inspect_button {
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }

            QFrame#toggle_frame QPushButton:checked {
                background-color: #770ecc;
                color: #fff;
                border: 1px solid #8f14f5;
            }
        """
        self.toggle_frame.setStyleSheet(qss)
        # CRITICAL: Sometimes you need to force a style polish update
        self.toggle_frame.style().unpolish(self.toggle_frame)
        self.toggle_frame.style().polish(self.toggle_frame)
        self.toggle_frame.update()

    def configure_plots(self):

        self.exp_plot_dataline = self.data_plot.plot([], pen='yellow')
        self.fit_dataline = self.data_plot.plot([], pen="cyan")
        self.data_plot.setLabel('left', 'Counts')

        self.residuals_dataline = self.residuals_plot.plot([], pen="yellow")
        self.residuals_plot.setTitle("Fit Residuals")

        self.preview_dataline = self.data_preview_plot.plot([], pen="yellow")

        rect = QRectF(0, 0, 1, 1)

        self.heatmap.getViewBox().setAspectLocked(True)

        self.image_item = pg.ImageItem(axisOrder='row-major')
        self.image_item.setImage(np.zeros((10, 10)))
        self.image_item.setRect(rect)

        self.heatmap.addItem(self.image_item)
        self.colorbar = self.heatmap.addColorBar(
            self.image_item, colorMap=pg.colormap.getFromMatplotlib('inferno')
        )

    def _on_toggle_clicked(self, button):
        if button == self.inspect_button:
            self.preview_index = 2
            self.preview_stackedwidget.setCurrentIndex(self.preview_index)
        else:
            current_tree_item = self.imported_data_tree.currentItem()
            path = current_tree_item.data(0, Qt.UserRole)
            if not path:
                return
            self.request_preview_sig.emit(path)

    def _select_model(self):

        model = self.models_combobox.currentText()
        self.select_model_sig.emit(model)

    def _select_axis_data(self):

        x_axis = self.x_axis_combobox.currentText()
        y_axis = self.y_axis_combobox.currentText()
        self.data_plot.setLabel("left", y_axis)
        self.data_plot.setLabel("bottom", x_axis)

        self.residuals_plot.setLabel("left", y_axis)
        self.residuals_plot.setLabel("bottom", x_axis)

        x_path = self.axis_options_path[x_axis]
        y_path = self.axis_options_path[y_axis]

        self.request_data_sig.emit(x_path, y_path)

    @Slot(DataResult, DataResult)
    def update_data_plot(self, x_data, y_data):

        self.exp_plot_dataline.setData(x_data.data, y_data.data)

    @Slot(dict)
    def update_imported_data_tree(self, structure):

        self.imported_data_tree.clear()
        self.x_axis_combobox.clear()
        self.y_axis_combobox.clear()
        self.axis_options_path = {}
        
        # We start from the root "/"
        root_item = QTreeWidgetItem(self.imported_data_tree, ["/"])
        root_item.setData(0, Qt.UserRole, "/")
        
        self._add_tree_nodes(structure["/"].get("children", {}), root_item)
        self.imported_data_tree.expandAll()

    def _add_tree_nodes(self, data, parent_item):
        for name, info in data.items():
            # Create the tree item with the name (e.g., 'Exp_001')
            item = QTreeWidgetItem(parent_item, [name])
            
            # Store the full HDF5 path (e.g., '/Data/Pulsed/Exp_001')
            # This is vital for the Dataclass request later
            current_path = f"{parent_item.data(0, Qt.UserRole)}/{name}".replace("//", "/")
            item.setData(0, Qt.UserRole, current_path)
            
            # If it's a group, recurse to add its children
            if info["type"] == "Group":
                self._add_tree_nodes(info.get("children", {}), item)
            if info["type"] == "Dataset" and info.get("shape", False):
                self._add_axis_options(name, info, current_path)

    
    def _add_axis_options(self, name: str, info: dict, path: str):

        if "Analysis" not in path.strip("/"):
            if len(info["shape"]) == 1:
                self.axis_options_path[name] = path
                self.x_axis_combobox.addItem(name)
                self.y_axis_combobox.addItem(name)

    @Slot(list)
    def update_parameters_table(self, params):

        self.parameters_table.setRowCount(len(params))
        self.parameters_table.setColumnCount(5)
        self.parameters_table.setHorizontalHeaderLabels(
            ["Parameter", "Value", "Fixed", "Min", "Max"])
        for i, param in enumerate(params):
            # Column 0: Name   
            name_item = QTableWidgetItem(param["name"])
            self.parameters_table.setItem(i, 0, name_item)
            
            # Column 1: Value (Editable)
            val_item = QTableWidgetItem(f"{param['value']:.4f}")
            self.parameters_table.setItem(i, 1, val_item)
            
            # Column 2: Fixed Checkbox
            check_item = QTableWidgetItem()
            check_item.setCheckState(Qt.Unchecked if param['vary'] else Qt.Checked)
            self.parameters_table.setItem(i, 2, check_item)
            
            # Column 3: Display min for reference
            min_item = QTableWidgetItem(f"{param['min']}")
            self.parameters_table.setItem(i, 3, min_item)

             # Column 3: Display max for reference
            max_item = QTableWidgetItem(f"{param['max']}")
            self.parameters_table.setItem(i, 4, max_item)

    def _on_tree_selection_changed(self, current, previous):

        path = current.data(0, Qt.UserRole)
        if not path:
            return

        # Request inspect info to the logic
        if self.inspect_button.isChecked():
            self.request_inspect_info_sig.emit(path)

        elif self.display_button.isChecked():
            self.request_preview_sig.emit(path)

    @Slot(dict)
    def update_inspect_info(self, info: InspectInfo):

        self._clear_inspect_layout()

        kind = "Dataset" if info.is_dataset else "Group"
        kind_layout = QHBoxLayout()
        kind_label = QLabel(kind)
        kind_label.setStyleSheet("font-size: 10pt;")
        kind_layout.addWidget(kind_label)
        kind_layout.setContentsMargins(0, 5, 0, 5)
        self.inspect_layout.addRow(kind_layout)
        
        self.inspect_layout.addRow("Path", QLabel(info.path))
        self.inspect_layout.addRow("Name", QLabel(info.name))

        if info.is_dataset:
            self.inspect_layout.addRow("Shape", QLabel(str(info.shape)))
            dtype = info.dtype + ", " + str(info.size_bytes) + ", " + str(info.byte_order)
            self.inspect_layout.addRow("Type", QLabel(dtype))

        if info.attributes:
        
            attr_layout = QHBoxLayout()
            attr_label = QLabel("Attributes")
            attr_label.setStyleSheet("font-size: 10pt;")
            attr_layout.addWidget(attr_label)
            attr_layout.setContentsMargins(0, 5, 0, 5)
            self.inspect_layout.addRow(attr_layout)

            for key, value in info.attributes.items():
                self.inspect_layout.addRow(key, QLabel(str(value)))

        self.preview_index = 2
        self.inspect_button.click()

    def _clear_inspect_layout(self):
        """Removes all widgets from the inspect layout."""
        while self.inspect_layout.rowCount() > 0:
            self.inspect_layout.removeRow(0)

    @Slot(DataResult)
    def update_preview_plot(self, data: DataResult):
        if data.ndim == 1:
            self.preview_index = 0
            self.preview_dataline.setData(data.data)
        elif data.ndim == 2:
            self.preview_index = 1
            self._update_preview_img(data.data)
        elif data.ndim == 3:
            self.preview_index = 1
            self._update_preview_img(data.data[:, :, 0])

        self.preview_stackedwidget.setCurrentIndex(self.preview_index)

    def _update_preview_img(self, img):

        img = np.array(img)
        self.image_item.setImage(np.flip(img, 0))
        self.colorbar.setLevels((np.min(img), np.max(img)))

    @Slot(np.ndarray, np.ndarray)
    def plot_fit_data(self, x_data, fit_data):

        self.fit_dataline.setData(x_data, fit_data)

    @Slot(np.ndarray, np.ndarray)
    def plot_fit_residuals(self, x_data, residuals):

        self.residuals_dataline.setData(x_data, residuals)

    @Slot(str)
    def update_fit_report(self, report):

        self.fit_report_label.setText(report)


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication
    print(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    import artwork.qudi_icons_rc
    from qudi.logic.pulsed_exp_logic import Pulse

    app = QApplication(sys.argv)
    window = AnalyzerMainWindow()
    window.show()

    data = {
        'pl_mean': np.random.random(100),
        'pl_raw_mean': np.random.random((10, 10, 2)),
        'pl_raw_std': np.random.random((10, 10, 2)),
        'pl_std': np.random.random(100),
        'tau': np.random.random(100)
    }
    metadata = {'iterations': 30, 'loop': 10000, 'repeat_exp': 10, 'sequence': 'T1laser'}
    general = {
        'column_dtypes': np.array([b'float64', b'float64', b'float64', b'float64', b'float64'], dtype='|S7'),
        'column_headers': np.array(['tau', 'pl_raw_mean', 'pl_raw_std', 'pl_mean', 'pl_std'], dtype=object),
        'notes': 'This are some notes',
        'steps': np.array([10, 30]),
        'timestamp': '2026-04-09T13:58:15.277085'
    }

    tree = {
        '/': {
            'type': 'Group',
            'children': {
                'Analysis': {
                    'type': 'Group',
                    'children': {
                        '20260416-1304-53_SingleExponential': {
                            'type': 'Group',
                            'children': {
                                'ModelTraces': {
                                    'type': 'Group',
                                    'children': {
                                        'fit_x': {'type': 'Dataset', 'shape': (30,)},
                                        'fit_y': {'type': 'Dataset', 'shape': (30,)},
                                        'residuals': {'type': 'Dataset', 'shape': (30,)},
                                        'x': {'type': 'Dataset', 'shape': (30,)},
                                        'y': {'type': 'Dataset', 'shape': (30,)}
                                    }
                                },
                                'parameters': {'type': 'Dataset'},
                                'report': {'type': 'Dataset'}
                            }
                        }
                    }
                },
                'Data': {
                    'type': 'Group',
                    'children': {
                        'pl_mean': {'type': 'Dataset', 'shape': (30,)},
                        'pl_raw_mean': {'type': 'Dataset', 'shape': (10, 30, 2)},
                        'pl_raw_std': {'type': 'Dataset', 'shape': (10, 30, 2)},
                        'pl_std': {'type': 'Dataset', 'shape': (30,)},
                        'tau': {'type': 'Dataset', 'shape': (30,)}
                    }
                }
            }
        }
    }
    window.update_imported_data_tree(tree)
    sys.exit(app.exec_())
