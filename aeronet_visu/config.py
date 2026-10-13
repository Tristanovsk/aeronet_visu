'''
Package configuration: absolute and relative paths used in the package.

* ``root``: absolute path of the :mod:`aeronet_visu` package directory
* ``F0_file``: solar spectral irradiance file (Thuillier et al., 2003, 0.3 nm resolution)
'''
import os
import numpy as np

root = os.path.dirname(os.path.abspath(__file__))
F0_file =  os.path.join(root, '../auxdata/Thuillier_2003_0.3nm.dat')

