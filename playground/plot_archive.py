import os
import glob

import numpy as np
import pandas as pd
import xarray as xr
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
import colorcet as cc

plt.rcParams.update({'font.family': 'Times New Roman',
                     'font.size': 18, 'axes.labelsize': 20,
                     })
rc = {"font.family": "serif",
      "mathtext.fontset": "stix"}
plt.rcParams.update(rc)
plt.rcParams["font.serif"] = ["Times New Roman"] + plt.rcParams["font.serif"]
plt.ioff()
from aeronet_visu import data_loading as dl

opj = os.path.join

def get_month(imonth):
    return datetime.date(1900, imonth, 1).strftime('%B')


figdir= '/DATA/AERONET/fig'
dir = '/DATA/AERONET/OCv3/'
sites = ['Abu_Al_Bukhoosh', 'ARIAKE_TOWER', 'Bahia_Blanca', 'Banana_River',
       'Bari_Waterfront', 'Blyth_NOAH', 'Casablanca_Platform',
       'Chesapeake_Bay', 'COVE_SEAPRISM', 'Gageocho_Station',
       'Galata_Platform', 'Gloria', 'Gotland', 'GOT_Seaprism', 'Grizzly_Bay',
       'Gustav_Dalen_Tower', 'HBOI', 'Helsinki_Lighthouse', 'Ieodo_Station',
       'Irbe_Lighthouse', 'KAUST_Campus', 'Kemigawa_Offshore', 'Lake_Erie',
       'Lake_Okeechobee', 'Lake_Okeechobee_N', 'LISCO', 'Lucinda', 'MVCO',
       'Palgrunden', 'PLOCAN_Tower', 'RdP-EsNM', 'Sacramento_River',
       'San_Marco_Platform', 'Section-7_Platform', 'Socheongcho',
       'South_Greenbay', 'Thornton_C-power', 'USC_SEAPRISM', 'USC_SEAPRISM_2',
       'Venise', 'WaveCIS_Site_CSI_6', 'Zeebrugge-MOW1']
# file = 'Venise_OCv3.lev20'
lev = '15'
param = 'Lwn'
info = []
for site in sites:
    file = site + '_OCv3.lev' + lev

    fig_file = opj(figdir, site + '_Rrs_from_'+param+'_OCv3_l'+lev+'.pdf')
    if os.path.exists(fig_file):
        continue
    print(site)
    # ---------------------------------------------
    # Load data and convert into xarray
    # ---------------------------------------------
    try:
        df = dl.Read(opj(dir, file)).read_aeronet_ocv3()
        start_date, end_date = df.index.min().strftime('%Y-%m-%d'), df.index.max().strftime('%Y-%m-%d')
        number = df.shape[0]
    except:
        continue
    print(site)
    irr = dl.Irradiance()
    irr.load_F0()

    df = df.droplevel(0, 1)
    # criteria to select scalar and spectrum values
    criteria = df.columns.get_level_values(1) == ''
    df_att = df.loc[:, criteria].droplevel(1, 1)
    df_spec = df.loc[:, ~criteria]

    ds = df_spec.stack().to_xarray()
    ds = xr.merge([ds, df_att.to_xarray()])
    del df

    ds = ds.assign_coords({'level_1': ds.level_1.astype(float)}).rename({'level_1': "wl"})
    ds['SZA'] = ds.Solar_Zenith_Angle.mean(axis=1)
    ds['season'] = ds['date.season']

    wl = ds.wavelength * 1000
    ds['Rrs'] = ds[param] / (irr.get_F0(wl) * 0.1)
    ds=ds.sortby('wl')
    cols = 3
    rows = 4  # len(np.unique(ds['date.year']))
    fpdf = []
    cparam = 'SZA'
    cmap = cc.cm.bkr
    norm = mpl.colors.Normalize(vmin=20, vmax=60)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])


    with PdfPages(fig_file) as pdf:
        for iyear, (year, ds_) in enumerate(ds.groupby('date.year')):
            print(year)
            fig, axs = plt.subplots(nrows=rows, ncols=cols, sharex=True, figsize=(16, rows * 5.75), sharey=True)
            fig.subplots_adjust(hspace=0.2, wspace=0.1)
            axs_ = axs.ravel()
            [axi.set_axis_off() for axi in axs_]
            for imonth, (month, ds__) in enumerate(ds_.groupby('date.month')):
                axs_[month - 1].set_axis_on()
                axs_[month - 1].set_title(get_month(month) + '-' + str(year))
                axs_[month - 1].minorticks_on()

                for _, d_ in ds__.groupby('date'):
                    d_=d_.dropna('wl')
                    axs_[month - 1].plot(d_.wl, d_.Rrs, color=cmap(norm(d_[cparam])), lw=1,
                                         alpha=0.5)  # ,cmap=cc.cm.bgyw)
                axs_[month - 1].set_ylabel('')

            cb = fig.colorbar(sm, ax=axs, shrink=0.5, aspect=35, pad=0.05, location='top')
            cb.set_label('SZA (deg)', fontsize=22)
            pdf.savefig()