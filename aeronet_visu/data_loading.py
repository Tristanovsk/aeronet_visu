'''
Readers for AERONET and AERONET-OC data files and solar irradiance utilities.

All readers return a :class:`pandas.DataFrame` indexed by acquisition date
(``date``) with three-level :class:`pandas.MultiIndex` columns:

* ``l0``: original column name of the AERONET file,
* ``l1``: data type (e.g., ``aot``, ``std``, ``wavelength``, ``Lwn``),
  empty string for non-spectral parameters,
* ``l2``: wavelength in nm for spectral parameters, empty string otherwise.

Example::

    from aeronet_visu import data_loading as dl
    df = dl.Read('Venise_OC.lev20').read_aeronet_oc()
'''

import os
import pandas as pd
import numpy as np
import re
import datetime as dt
from scipy.interpolate import interp1d

from .config import *


class Read:
    '''
    Reader for AERONET and AERONET-OC text files.

    :param file: path to the AERONET file, or file-like object (e.g., :class:`io.StringIO`)
    '''

    def __init__(self,file):
        self.file = file

    def read_aeronet_ocv3(self, skiprows=8):
        '''
        Read and format in pandas data.frame the AERONET-OC Version 3 data
        (format distributed by the AERONET website).

        :param skiprows: number of header lines before the data table
        :return: data with date index and (``l0``, ``l1``, ``l2``) MultiIndex columns
        :rtype: pandas.DataFrame
        '''

        dateparse = lambda x: pd.datetime.strptime(x, "%d:%m:%Y %H:%M:%S")
        ifile=self.file

        h1 = pd.read_csv(ifile, skiprows=skiprows - 1, nrows=1).columns[3:]
        h1 = np.insert(h1,0,'site')
        data_type = h1.str.replace('\[.*\]', '')
        data_type = data_type.str.replace('Exact_Wave.*', 'wavelength')
        #convert into float to order the dataframe with increasing wavelength
        h2 = h1.str.replace('.*\[', '')
        h2 = h2.str.replace('nm\].*', '')
        h2 = h2.str.replace('Exact_Wavelengths\(um\)_','')
        h2 = pd.to_numeric(h2, errors='coerce') #h2.str.extract('(\d+)').astype('float')
        h2 = h2.fillna('').T
        df = pd.read_csv(ifile, skiprows=skiprows, na_values=['N/A', -999.0,-9.999999 ], parse_dates={'date': [1, 2]},
                         date_parser=dateparse, index_col=False)

        # df['site'] = site
        # df.set_index(['site', 'date'],inplace=True)
        df.set_index('date', inplace=True)

        tuples = list(zip(h1, data_type, h2))
        df.columns = pd.MultiIndex.from_tuples(tuples, names=['l0', 'l1', 'l2'])
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.columns = pd.MultiIndex.from_tuples([(x[0], x[1], x[2]) for x in df.columns])
        df.sort_index(axis=1, level=2, inplace=True)
        return df

    def read_aeronet_oc(self, skiprows=13):
        '''
        Read and format in pandas data.frame the standard AERONET-OC data
        (former Version 2 format, e.g. ``<site>_OC.lev20``).

        :param skiprows: number of header lines before the data table
        :return: data with date index and (``l0``, ``l1``, ``l2``) MultiIndex columns
        :rtype: pandas.DataFrame
        '''

        dateparse = lambda x: pd.datetime.strptime(x, "%d:%m:%Y %H:%M:%S")
        ifile=self.file
        h1 = pd.read_csv(ifile, skiprows=skiprows - 2, nrows=1).columns[2:]
        h2 = pd.read_csv(ifile, skiprows=skiprows - 1, nrows=1).columns[2:]
        h1 = h1.append(h2[len(h1):])
        data_type = h1.str.replace('\(.*\)', '', regex=True)
        data_type = data_type.str.replace('ExactWave.*', 'oc_wavelength')
        #convert into float to order the dataframe with increasing wavelength
        h2 = h2.str.extract('(\d+)').astype('float')
        h2 = h2.fillna('')
        df = pd.read_csv(ifile, skiprows=skiprows, na_values=['N/A', -999.0,-9.999999 ], parse_dates={'date': [0, 1]},
                         date_parser=dateparse, index_col=False)

        # df['site'] = site
        # df.set_index(['site', 'date'],inplace=True)
        df.set_index('date', inplace=True)

        tuples = list(zip(h1, data_type, h2))
        df.columns = pd.MultiIndex.from_tuples(tuples, names=['l0', 'l1', 'l2'])
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.sort_index(axis=1, level=2, inplace=True)
        return df


    def read_aeronet(self, skiprows=6):
        '''
        Read and format in pandas data.frame the V3 AERONET data
        (e.g., AOD or SDA files: ``<site>_aod_V3.lev20``, ``<site>_sda_V3.lev20``).

        Spectral columns are labelled ``aot`` (aerosol optical thickness), ``std``
        (triplet standard deviation) and ``wavelength`` (exact wavelength, converted
        into nm).

        :param skiprows: number of header lines before the data table
        :return: data with date index and (``l0``, ``l1``, ``l2``) MultiIndex columns
        :rtype: pandas.DataFrame
        '''

        ifile=self.file
        df = pd.read_csv(ifile, skiprows=skiprows, nrows=1)  # read just first line for columns
        columns = df.columns.tolist()  # get the columns
        cols_to_use = columns[:len(columns) - 1]  # drop the last one
        df = pd.read_csv(ifile, skiprows=skiprows, usecols=cols_to_use, index_col=False, na_values=['N/A', -999.0])
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.rename(columns={'AERONET_Site_Name': 'site', 'Last_Processing_Date(dd/mm/yyyy)': 'Last_Processing_Date'},
                  inplace=True)
        format = "%d:%m:%Y %H:%M:%S"
        df['date'] = pd.to_datetime(df[df.columns[0]] + ' ' + df[df.columns[1]], format=format)
        # df.set_index(['site','date'], inplace=True)
        df.set_index('date', inplace=True)
        df = df.drop(df.columns[[0, 1]], axis=1)
        # df['year'] = df.index.get_level_values(1).year

        # cleaning up
        df.drop(list(df.filter(regex='Input')), axis=1, inplace=True)
        df.drop(list(df.filter(regex='Empty')), axis=1, inplace=True)
        df.drop(list(df.filter(regex='Day')), axis=1, inplace=True)

        # indexing columns with spectral values
        data_type = df.columns.str.replace('AOD.*nm', 'aot', regex=True)
        data_type = data_type.str.replace('Exact_Wave.*', 'wavelength', regex=True)
        data_type = data_type.str.replace('Triplet.*[0-9]', 'std', regex=True)
        data_type = data_type.str.replace(r'^(?!aot|std|wavelength).*$', '', regex=True)

        wl_type = df.columns.str.extract('(\d+)').astype('float')
        wl_type = wl_type.fillna('')

        tuples = list(zip(df.columns, data_type, wl_type))
        df.columns = pd.MultiIndex.from_tuples(tuples, names=['l0', 'l1', 'l2'])
        if 'wavelength' in df.columns.levels[1]:
            df.loc[:, (slice(None), 'wavelength',)] = df.loc[:, (slice(None), 'wavelength')] * 1000  # convert into nm
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.sort_index(axis=1, level=2, inplace=True)
        return df

    def read_aeronet_inv(self, skiprows=6):
        '''
        Read and format in pandas data.frame the V3 Aerosol Inversion AERONET data
        (e.g., refractive index or volume size distribution files:
        ``<site>_rin_V3.lev20``, ``<site>_vol_V3.lev20``).

        :param skiprows: number of header lines before the data table
        :return: data with date index and (``l0``, ``l1``, ``l2``) MultiIndex columns
        :rtype: pandas.DataFrame
        '''
        ifile=self.file
        df = pd.read_csv(ifile, skiprows=skiprows, nrows=1)  # read just first line for columns
        columns = df.columns.tolist()  # get the columns
        cols_to_use = columns[:len(columns) - 1]  # drop the last one
        df = pd.read_csv(ifile, skiprows=skiprows, usecols=cols_to_use, index_col=False, na_values=['N/A', -999.0])
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.rename(columns={'AERONET_Site_Name': 'site', 'Last_Processing_Date(dd/mm/yyyy)': 'Last_Processing_Date',},
                  inplace=True)
        format = "%d:%m:%Y %H:%M:%S"
        df['date'] = pd.to_datetime(df[df.columns[1]] + ' ' + df[df.columns[2]], format=format)
        # df.set_index(['site','date'], inplace=True)
        df.set_index('date', inplace=True)
        df = df.drop(df.columns[[0, 1]], axis=1)
        # df['year'] = df.index.get_level_values(1).year

        # cleaning up
        df.drop(list(df.filter(regex='Input')), axis=1, inplace=True)
        df.drop(list(df.filter(regex='Empty')), axis=1, inplace=True)
        df.drop(list(df.filter(regex='Day')), axis=1, inplace=True)
        df.drop(list(df.filter(regex='Angle_Bin')), axis=1, inplace=True)


        # indexing columns with spectral values
        data_type = df.columns.str.replace('AOD.*nm', 'aot')
        data_type = data_type.str.replace('Exact_Wave.*', 'wavelength')
        data_type = data_type.str.replace('Triplet.*[0-9]', 'std')
        data_type = data_type.str.replace(r'^(?!aot|std|wavelength).*$', '')

        wl_type = df.columns.str.extract('(\d+)').astype('float')
        wl_type = wl_type.fillna('')

        tuples = list(zip(df.columns, data_type, wl_type))
        df.columns = pd.MultiIndex.from_tuples(tuples, names=['l0', 'l1', 'l2'])
        if 'wavelength' in df.columns.levels[1]:
            df.loc[:, (slice(None), 'wavelength',)] = df.loc[:, (slice(None), 'wavelength')] * 1000  # convert into nm

        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.sort_index(axis=1, level=2, inplace=True)

        return df



class Irradiance:
    '''
    Extraterrestrial solar spectral irradiance (Thuillier et al., 2003).

    :param F0_file: path to the solar irradiance file
        (default: ``auxdata/Thuillier_2003_0.3nm.dat``, see :mod:`aeronet_visu.config`)

    Example::

        F0 = Irradiance()
        F0.load_F0()
        F0.get_F0([443, 560, 665])
    '''

    def __init__(self, F0_file=F0_file):
        self.F0_file = F0_file

    def load_F0(self, ):
        '''
        Load the solar irradiance file into ``self.F0df``
        (:class:`pandas.DataFrame` with columns ``wl`` in nm and ``F0`` in mW/m2/nm).
        '''
        self.F0df = pd.read_csv(self.F0_file, skiprows=15, sep='\t', header=None, names=('wl', 'F0'))

    def get_F0(self, wl, mute=False):
        '''
        Interpolate and return solar spectral irradiance (mW/m2/nm).

        :meth:`load_F0` must be called first. Results are stored in ``self.wl`` and ``self.F0``.

        :param wl: wavelength in nm, scalar or np.array
        :param mute: if True, values are not returned (only saved in object)
        :return: solar irradiance at ``wl`` in mW/m2/nm (None if ``mute`` is True)
        :rtype: numpy.ndarray
        '''
        self.wl = wl
        self.F0 = interp1d(self.F0df.wl, self.F0df.F0, fill_value='extrapolate')(wl)

        if not mute:
            return self.F0
