# qudi-addon-template
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

A template repository to create your own pip-installable qudi namespace addon packages.

Replace this README.md with your own projects' readme.

> __WARNING:__
> 
> Do __NOT__ put any `__init__.py` files into qudi namespace packages. Doing so will prevent any 
> addon packages to install additional modules into the respective package or any sub-packages.
> 
> You can however create your own non-namespace packages (including `__init__.py`). Just make sure 
> you do not want to install any addons later on in this package or any sub-packages thereof.
