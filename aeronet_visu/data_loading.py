import os
import pandas as pd
import re


class read:
    def __init__(self,file):
        self.file = file


    def read_aeronet_oc(self, skiprows=13):
        ''' Read and format in pandas data.frame the standard AERONET-OC data '''

        dateparse = lambda x: pd.datetime.strptime(x, "%d:%m:%Y %H:%M:%S")
        ifile=self.file
        h1 = pd.read_csv(ifile, skiprows=skiprows - 2, nrows=1).columns[2:]
        h2 = pd.read_csv(ifile, skiprows=skiprows - 1, nrows=1).columns[2:]
        h1 = h1.append(h2[len(h1):])
        data_type = h1.str.replace('\(.*\)', '')
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
        ''' Read and format in pandas data.frame the V3 AERONET data '''

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

    def read_aeronet_inv(self, skiprows=6):
        ''' Read and format in pandas data.frame the V3 Aerosol Inversion AERONET data '''
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