import os
import glob

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib as mpl

plt.rcParams.update({'font.family': 'Times New Roman',
                     'font.size': 18, 'axes.labelsize': 20,
                     })
rc = {"font.family": "serif",
      "mathtext.fontset": "stix"}
plt.rcParams.update(rc)
plt.rcParams["font.serif"] = ["Times New Roman"] + plt.rcParams["font.serif"]

from aeronet_visu import data_loading as dl

opj = os.path.join

dir = '/DATA/AERONET/OCv3/'
sites = ['Abu_Al_Bukhoosh', 'ARIAKE_TOWER', 'Bahia_Blanca', 'Banana_River', 'Bari_Waterfront', 'Blyth_NOAH',
         'Casablanca_Platform', 'Chesapeake_Bay', 'COVE_SEAPRISM', 'Gageocho_Station', 'Galata_Platform', 'Gloria',
         'Gotland', 'GOT_Seaprism', 'Grizzly_Bay', 'Gustav_Dalen_Tower', 'HBOI', 'Helsinki_Lighthouse', 'Ieodo_Station',
         'Irbe_Lighthouse', 'KAUST_Campus', 'Kemigawa_Offshore', 'Lake_Erie', 'Lake_Okeechobee', 'Lake_Okeechobee_N',
         'LISCO', 'Lucinda', 'MVCO', 'Palgrunden', 'PLOCAN_Tower', 'RdP-EsNM', 'Sacramento_River', 'San_Marco_Platform',
         'Section-7_Platform', 'Socheongcho', 'South_Greenbay', 'Thornton_C-power', 'USC_SEAPRISM', 'USC_SEAPRISM_2',
         'Venise', 'WaveCIS_Site_CSI_6', 'Zeebrugge-MOW1']
# file = 'Venise_OCv3.lev20'
lev = '15'
info = []
for site in sites:
    file = site + '_OCv3.lev' + lev
    print(site)

    # ---------------------------------------------
    # Load data and convert into xarray
    # ---------------------------------------------
    try:
        df = dl.Read(opj(dir, file)).read_aeronet_ocv3()
        start_date, end_date = df.index.min().strftime('%Y-%m-%d'), df.index.max().strftime('%Y-%m-%d')
        number = df.shape[0]
    except:
        start_date, end_date = '2015-07-01','2015-07-01'
        number = 0
    info.append([site,start_date,end_date,number])

df = pd.DataFrame(info,columns=['site','start_date','end_date','number'])



df.to_csv('/DATA/AERONET/info_aeronet_oc_v'+lev+'_v2.csv',index=False)

