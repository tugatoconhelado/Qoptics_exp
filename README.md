# Qoptics_exp
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

A collection of measurement modules for [qudi](https://github.com/Ulm-IQO/qudi-core).

These modules are designed to provide control for quantum optics devices and experiments.

## Installation

In the current stage of development, for a development installation, the recommended way of installing would be via an editable pip install. In the root folder of the project:

> pip install -e .

Note: It is recommended to setup a virtual environment at least while the program is not 100% finished.

This should install all dependencies and provide some command line scripts for easy access to the software. In order to run the program, execute qudi on a terminal with the environment activated.


> __WARNING:__
> 
> Do __NOT__ put any `__init__.py` files into qudi namespace packages. Doing so will prevent any 
> addon packages to install additional modules into the respective package or any sub-packages.
> 
> You can however create your own non-namespace packages (including `__init__.py`). Just make sure 
> you do not want to install any addons later on in this package or any sub-packages thereof.


## Requisites

The module will install the python libraries it requires when installing. These are:

- `numpy`
- `matplotlib`
- `nidaqmx`
- `PySide2`
- `pyqtgraph`
- `seabreeze`
- `h5py`

It has to be noted that in order for `nidaqmx` to work, the National Instruments dll files have to be installed on your computer.

## Contributing

This section aims at describing the general design of the software an all its components.

### Project Structure

The project is structured as a [qudi](https://github.com/Ulm-IQO/qudi-core) module. For more information on how they are structured you can also consult [this paper](https://doi.org/10.1016/j.softx.2017.02.001). An experiment module basically consists of three types of modules:

- `gui`: Handles the graphical user interface
- `logic`: Performs all the logic in the experiment
- `hardware`: Controls the data acquisition hardware

The file structure of the project is:

    - artwork
        - icons
        - styles
    - docs
    - src
        - qudi
            - gui
            - logic
            - interface
            - hardware

The `artwork` directory just contains icons used for the gui and styles to theme it. The code that actually contains the modules is contained inside the `qudi` subdirectories.


