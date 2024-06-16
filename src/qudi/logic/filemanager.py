"""
Provides a collection of core utilities to load files.

It essentially grabs file paths to load in different ways
and provides a simple function to load json files.

Contains the following functions:

- get_load_file_path_from_dialog(parent, file_dir)
- load_json(file_path)
- get_file_path_iteratively(current_file, file_dir, iterate)
"""
import os
import json
import datetime
import numpy as np
from PySide2.QtWidgets import QFileDialog
from PySide2.QtCore import QObject
import h5py
from qudi.util.datastorage import DataStorageBase


class HDF5DataStorage(DataStorageBase):
    
    
    def __init__(self, *, root_dir, comments='# ', delimiter='\t', file_extension='.dat',
                column_formats=None, **kwargs):
        
        super().__init__(root_dir=root_dir, **kwargs)

        self._file_extension = ''
        self._delimiter = '\t'
        self.file_extension = file_extension
        self.delimiter = delimiter
        self.comments = comments if isinstance(comments, str) else None
        self.column_formats = column_formats

    @property
    def file_extension(self):
        return self._file_extension

    @file_extension.setter
    def file_extension(self, value):
        if (value is not None) and (not isinstance(value, str)):
            raise TypeError('file_extension must be str or None')
        if not value:
            self._file_extension = ''
        elif value.startswith('.'):
            self._file_extension = value
        else:
            self._file_extension = '.' + value

    @property
    def delimiter(self):
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value):
        if not isinstance(value, str) or value == '':
            raise ValueError('delimiter must be non-empty string')
        self._delimiter = value
    
    def load_data(self, filename):
        
        if os.path.splitext(filename)[1] != self.file_extension:
            raise ValueError(f'File {filename} is not a valid {self.file_extension} file')
        else:
            with h5py.File(filename, 'r') as file:
                data_group = file['Data']
                general = dict(file.attrs)
                metadata = dict(data_group.attrs)
                data = {}
                column_mdata = []
                for name, dataset in data_group.items():
                    data[name] = np.array(dataset[()])
                    column_mdata.append(dict(dataset.attrs))
                file.close()
            return data, metadata, general, filename
        

    def save_data(self, data: dict = None, timestamp=None, metadata: dict = None, notes: str = '', nametag=None,
                  column_headers=None, column_dtypes=None, column_mdata=None, filename=None):

        # Checks for timestamp
        if timestamp is None:
            timestamp = datetime.datetime.now()
    
        # Creates the filename
        if filename is None:
            datetime_str = timestamp.strftime('%Y%m%d-%H%M-%S')
            if nametag is not None:
                filename = f'{datetime_str}_{nametag}{self.file_extension}'
                filename = os.path.join(self.root_dir, filename)

        # Checks for column dtypes
        if column_dtypes is None:
            column_dtypes = ()
            for value in data.values():
                column_dtypes += (value.dtype,)
        dtype_array = np.array([str(dtype) for dtype in column_dtypes])

        # Checks for column headers
        if column_headers is None:
            column_headers = tuple(data.keys())

        # General file metadata
        general = {
            'timestamp': timestamp.isoformat(),
            'column_dtypes': dtype_array.astype('S'),
            'column_headers': column_headers,
            'notes': notes,
            'steps': (10, 30)
        }

        # Write to file
        with h5py.File(filename, 'w') as file:
            file.attrs.update(general)
            data_group = file.create_group('Data')
            data_group.attrs.update(metadata) # Adds measurement parameters
            for i in range(len(data.keys())):
                name = list(data.keys())[i]
                value = list(data.values())[i]
                data_set = data_group.create_dataset(name, data=value, dtype=column_dtypes[i])
                data_set.attrs.update(column_mdata[i] if column_mdata is not None else {})
        return filename

def get_load_file_path_from_dialog(parent=None, file_dir: str = 'data'):
    """
    Generates a File Dialog to select file to load.

    Parameters
    ----------
    parent : ExperimentGui
        Or an instance QWidget that will be the parent for the QFileDialog
    file_dir : str, optional
        Path of the directory in which to start the file dialog. Default :
        'data'

    Returns
    -------
    file_path : str
        Indicates the path of the file selected or '' if none was selected
    """
    dialog = QFileDialog(parent)
    directory = file_dir
    dialog.setDirectory(directory)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setNameFilter('HDF5 data files (*.h5)')
    dialog.setViewMode(QFileDialog.ViewMode.Detail)
    if dialog.exec_():
        file_path = dialog.selectedFiles()[0]
        file_type = dialog.selectedNameFilter()
    else:
        return ''
    return os.path.abspath(file_path)

def load_json(file_path) -> dict:
    """
    Loads a json file

    Parameters
    ----------
    file_path : str
        Path of the file to be loaded

    Returns
    -------
    loaded_data : dict
        Content of the json file as a dict
    """
    with open(file_path, 'r') as file:
        loaded_data = json.load(file)

    return loaded_data

def get_file_path_iteratively(current_file : str = '', file_dir : str = 'test',
        iterate=-1) -> str:
    """
    Loads a previous or next file with respect to the current file.

    It looks based on the value of position. The search is in the current
    save directory. If the current file is '' it loads the last file in
    the folder.

    Parameters
    ----------
    current_file : int
        Name of the current file, if '' it will consider the current file
        as the last file in the file_dir
    file_dir : str, optional
        Path of the directory in which to look for files. Default : 'test'
    iterate : int, optional
        Indicates to move to next (position = 1) or previous file
        (position = -1). It can only take values 1 or -1. Default : -1

    Returns
    -------
    file_path : str
        Name of the file loaded or '' if no file was found.
    """
    directory = file_dir
    files = [os.path.join(directory, file) for file in os.listdir(directory)]
    if len(files) == 0:
        return ''
    
    # If no file has been saved or loaded the current file is the
    # last in the directory (the latest saved file)
    if current_file == '':
        current_file = files[-1]
        iterate = 0

    if current_file in files:
        # Gets the cycling over the files (4%4=0, 5%4=1, ...)
        new_file_index = (files.index(current_file) + iterate ) % len(files)
    else:
        new_file_index = -1
    file_path = files[new_file_index]
    return file_path

def save_dict_to_json(data : dict, file_path : str) -> str:
    """
    Saves data dict to json.

    Parameters
    ----------
    data : dict
        Dict form of the data to be saved
    file_path : str
        Path of the file to be saved

    Returns
    -------
    file_path : str
        The path of the saved file
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
    return file_path

def get_file_path_to_save(
        save_dir : str = 'test',
        filename : str = 'experiment_data',
        exp_str : str = 'EXPData',
        add_timestamp: bool = True) -> str:
    """
    Constructs a file path for the data to be saved

    Parameters
    ----------
    save_dir : str, optional
        Directory to save the data. Default = 'test'
    filename : str, optional
        Name for the file, will only be used if add_timestamp = False.
        Default : 'experiment_data'
    exp_str : str, optional
        If add_timestamp is True, this string will be added as a prefix to
        the saved file. Default : 'EXPData'
    add_timestamp : bool, optional
        Indicates wether to save the file registering the current time. If
        True it will set the filename to the exp_str + current_time + .json.
        Default : True

    Returns
    -------
    file_path : str
        The path of the saved file as save_dir + file_name.

    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if add_timestamp:
        file_path = os.path.join(save_dir, exp_str + current_time)
    else:
        file_path = os.path.join(save_dir, filename)

    return file_path

def get_save_file_path_from_dialog(parent=None, file_dir: str = 'data'):
    """
    Generates a File Dialog to select file to save.

    Parameters
    ----------
    parent : ExperimentGui
        Or an instance QWidget that will be the parent for the QFileDialog
    file_dir : str, optional
        Path of the directory in which to start the file dialog. Default :
        'data'

    Returns
    -------
    file_path : str
        Indicates the path for the file to save.
    """
    dialog = QFileDialog(parent)
    directory = file_dir
    dialog.setDirectory(directory)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setNameFilter('HDF5 data files (*.h5)')
    dialog.setViewMode(QFileDialog.ViewMode.Detail)
    dialog.setDefaultSuffix('h5')
    if dialog.exec_():
        file_path = dialog.selectedFiles()[0]
        file_type = dialog.selectedNameFilter()
    else:
        return ''
    return os.path.abspath(file_path)


class FileManager(QObject):
    """
    Save and load data to/from disk

    Attributes
    ----------
    data_loaded_signal : Signal(ExperimentData, str)
        Signal emitted when loading files
    data_saved_signal : Signal(ExperimentData, str)
        Signal emitted when saving files

    Methods
    -------
    __init__
        Constructor for the `FileManager` class
    get_path_for_experiment(experiment_name) : str
        Creates a directory for the experiment data inside the data directory
    save
        Saves the data to the experiment folder
    save_as NOT IMPLEMENTED
    load
        loads the data from a file dialog selected file
    load_previous
        Loads previous file in the experiment folder
    load_next
        Loads next file in the experiment folder
    """

    def __init__(
            self, data_dir: str = 'data', experiment_name: str = 'test',
            exp_str : str = 'TEST', parent = None
        ) -> None:

        super().__init__(parent)
        self.data_dir = data_dir
        self.save_dir = self.get_path_for_experiment(experiment_name)
        self.load_dir = self.get_path_for_experiment(experiment_name)
        self.exp_str = exp_str
        self.parent_gui = parent

        self.current_file = ''

    def get_path_for_experiment(self, experiment_name) -> str:
        """
        Creates a directory for the experiment data inside the data directory

        Parameters
        ----------
        experiment_name : str
            Name of the folder to be created.

        Returns
        -------
        directory : str
            Name of the created directory, in case the directory already exists
            it will return the absolute path to the directory
        """
        if not os.path.isabs(self.data_dir):
            self.data_dir = os.path.abspath(self.data_dir)
        
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        directory = os.path.join(self.data_dir, experiment_name)
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    def save(self, data, metadata, column_metadata=None, filepath=None):
        
        update_current_file = False
        if filepath is None:
            update_current_file = True
        data_storage = HDF5DataStorage(
            root_dir=self.save_dir,
            file_extension='.h5',
            delimiter='\t',
            comments='# ',
            column_formats=None
        )
        filepath = data_storage.save_data(
            data=data,
            timestamp=datetime.datetime.now(),
            metadata=metadata,
            notes='This are some notes',
            column_mdata=column_metadata,
            filename=filepath,
            nametag=self.exp_str
        )
        if update_current_file:
            self.current_file = filepath
        return filepath

    def save_as(self, data, metadata, column_metadata=None, filepath=None):

        file_path = get_save_file_path_from_dialog(
            file_dir=self.save_dir
        )
        if file_path != '':
            filepath = self.save(filepath=file_path, data=data, metadata=metadata, column_metadata=column_metadata)

            # If the file is outside data foler,
            # setting this will break the iteration
            #self.current_file = file_path 
            return filepath

    def load_file(self, filepath):

        data_storage = HDF5DataStorage(
            root_dir=self.load_dir,
            file_extension='.h5',
            delimiter='\t',
            comments='# ',
            column_formats=None
        )
        data, metadata, general, filepath = data_storage.load_data(filepath)
        return data, metadata, general, filepath
        
    def load(self):
        """
        Loads data from a dialog selected file.
        
        Calls `get_load_file_path_from_dialog` from `load` module to get the 
        file path, then it loads the json file with `load_json` function from
        `load` module. Finally, it calls the `from_dict` method from the
        `ExperimentData` instance. 
        
        After loading the data, it emits `data_loaded_signal` with the 
        data and the file_name loaded.
        """
        filepath = get_load_file_path_from_dialog(
            file_dir=self.load_dir
        )
        if filepath != '':
            data, metadata, general, filepath = self.load_file(filepath)
            head, file_name = os.path.split(filepath)
            
            # In case the you want the iteration dir to be same as save dir
            if head == self.save_dir:
                self.current_file = filepath
                self.load_dir = head
            #self.current_file = file_path
            #self.load_dir = head
            return data, metadata, general, filepath
        elif filepath == '':
            return {}, {}, {}, ''

    def load_previous(self):
        """
        Loads from the previous file in the experiment folder.
        
        Calls `get_file_path_iteratively` from `load` module to get the 
        previous file path, then it loads the json file with `load_json`
        function from `load` module. Finally, it calls the `from_dict` method
        from the`ExperimentData` instance. 
        
        After loading the data, it emits `data_loaded_signal` with the 
        data and the file_name loaded.
        """
        filepath = get_file_path_iteratively(
            current_file=self.current_file, file_dir=self.load_dir, iterate=-1
        )
        if filepath != '':
            data, metadata, general, filepath = self.load_file(filepath)
            self.current_file = filepath
            head, file_name = os.path.split(filepath)
            return data, metadata, general, filepath
        else:
            return {}, {}, {}, ''

    def load_next(self):
        """
        Loads from the next file in the experiment folder.
        
        Calls `get_file_path_iteratively` from `load` module to get the 
        next file path, then it loads the json file with `load_json`
        function from `load` module. Finally, it calls the `from_dict` method
        from the`ExperimentData` instance. 
        
        After loading the data, it emits `data_loaded_signal` with the 
        data and the file_name loaded.
        """
        filepath = get_file_path_iteratively(
            current_file=self.current_file, file_dir=self.load_dir, iterate=1
        )
        if filepath != '':
            data, metadata, general, filepath = self.load_file(filepath)
            self.current_file = filepath
            head, file_name = os.path.split(filepath)
            return data, metadata, general, filepath
        else:
            return {}, {}, {}, ''

    def delete(self, file):
        """
        Deletes the current file and loads the previous file.
        """
        if os.path.exists(file):
            os.remove(file)

if __name__ == '__main__':


    file_manager = FileManager()
    #file_manager.save()
    #file_manager.load()
    #file_manager.load_previous()
    #file_manager.load_next()
    #file_manager.delete()
    #file_manager.save_as()
    #file_manager.save_to_dat()