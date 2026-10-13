import os
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('tkagg')
import matplotlib.pyplot as plt

import invRrs
import glob
import os
import numpy as np
import pandas as pd
import geopandas as gpd

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

from invRrs import utils as u
from invRrs import solver

from aeronet_visu import data_loading as dl

opj = os.path.join

dir = '/DATA/AERONET/OCv3/'
file = 'Lake_Okeechobee_OCv3.lev20'
file = 'Grizzly_Bay_OCv3.lev20'
# file = 'Bahia_Blanca_OCv3.lev15'
# file = 'Banana_River_OCv3.lev15'
file = 'HBOI_OCv3.lev20'
sites = ['Abu_Al_Bukhoosh', 'ARIAKE_TOWER', 'Bahia_Blanca', 'Banana_River', 'Bari_Waterfront', 'Blyth_NOAH',
         'Casablanca_Platform', 'Chesapeake_Bay', 'COVE_SEAPRISM', 'Gageocho_Station', 'Galata_Platform', 'Gloria',
         'Gotland', 'GOT_Seaprism', 'Grizzly_Bay', 'Gustav_Dalen_Tower', 'HBOI', 'Helsinki_Lighthouse', 'Ieodo_Station',
         'Irbe_Lighthouse', 'KAUST_Campus', 'Kemigawa_Offshore', 'Lake_Erie', 'Lake_Okeechobee', 'Lake_Okeechobee_N',
         'LISCO', 'Lucinda', 'MVCO', 'Palgrunden', 'PLOCAN_Tower', 'Sacramento_River', 'San_Marco_Platform',
         'Section-7_Platform', 'Socheongcho', 'South_Greenbay', 'Thornton_C-power', 'USC_SEAPRISM', 'USC_SEAPRISM_2',
         'Venise', 'WaveCIS_Site_CSI_6', 'Zeebrugge-MOW1']
# file = 'Venise_OCv3.lev20'

site='LISCO'
lev = '15'

irr = dl.Irradiance()
irr.load_F0()

# ======================
# IOP_star for algae data
# =====================
chl_models = ['Bricaud1995', 'Ciotti2002_Sf005', 'Ciotti2002_Sf01',
              'Ciotti2002_Sf02', 'Ciotti2002_Sf03', 'Ciotti2002_Sf033',
              'Ciotti2002_Sf05', 'Gernez_Mesodinium']

aphy_star, bbphy_star = u.data().load_iop_phyto(chl_models[4])


file = site + '_OCv3.lev' + lev
odir = opj('/DATA/AERONET/OCv3_invRrs/fig', file.replace('.', '_'))
if not os.path.exists(odir):
    os.makedirs(odir)

param = 'Lwn'

# ---------------------------------------------
# Load data and convert into xarray
# ---------------------------------------------

df = dl.Read(opj(dir, file)).read_aeronet_ocv3()

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
ds = ds.sortby('wl')

# select the day to process
for day in range(29):
    date='2021-09-{:02}'.format(day+1)
    ds_day=ds.sel(date=date)
    if len(ds_day.date)<3:
        continue

    # ______
    # ---------------------------------
    # Set forward model parameters
    # ---------------------------------
    sza = 30
    density = 2.65
    wl = np.linspace(350, 1100, 200)
    model = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl)

    # ---------------------------------
    # Set forward model parameters
    # ---------------------------------
    filename = opj(odir, 'anisotopy_'+file.replace('.', '_') + '_' + date + '.png')
    fig, axs = plt.subplots(1, 3, figsize=(22, 6), sharex=True,sharey=True)
    i = 0
    res = []
    for name, ds_ in ds_day.groupby('date'):

        ds_ = ds_.dropna('wl')
        date = ds_.date.values

        if os.path.exists(filename):
            print("already processed")
            #continue
        # ds_ = ds.isel(date=333)
        wl = ds_.wavelength.values * 1000
        Rrs_meas = ds_[param].values  / (irr.get_F0(wl) * 0.1)
        Rrs_aeronet_iop = ds_['Lwn_IOP'].values / (irr.get_F0(wl) * 0.1)
        Rrs_aeronet_morel = ds_['Lwn_f/Q'].values / (irr.get_F0(wl) * 0.1)
        # remove deep blue
        # wl=wl[1:]
        # Rrs_meas=Rrs_meas[1:]

        sza = ds_.SZA.values
        if sza > 71.5:
            continue
        aot550 = ds_.Aerosol_Optical_Depth.interp(wl=550).values
        ws = ds_['Wind_Speed(m/s)'].values
        chl_a = ds_["Chlorophyll-a"].values
        vza, azi = 40, 90
        wl_simu = np.linspace(350, 1100, 200)

        chl, a_cdom, S_cdom, spm_norm, fine_prop = 2, 0.5, 0.015, 2, 0.5
        nr, ni_ref, S_ni = 1.17, -0.003, 0.005
        xinit = [chl, a_cdom, S_cdom, spm_norm, fine_prop, nr, ni_ref, S_ni]  # [0.1,2,2,0.015,0.5]

        simu = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl_simu)
        simu.set_coef(sza, vza, azi)
        Rrs_simu = simu.forward_model(xinit, output='Rrs')
        algo = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl)
        algo.set_coef(sza, vza, azi)

        # perform fit
        out = algo.call_solver(Rrs_meas, xinit=xinit, max_nfev=100)
        if out.aborted:
            x = out.last_internal_values  # continue
        else:
            x = out.x

        spm_est = density * (x[3])

        # save outcomes
        res.append([date, *x, spm_est])

        # spm_est_sd = density * np.sqrt(out.covar[3,3])
        # get parameters from forward model
        Rrs_simu, a_sed, bb_sed, a_bg, bb_tot, a_tot = simu.forward_model(x, output='all')
        simu.set_coef(0, 0, 90)
        Rrs_exact = simu.forward_model(x, output='Rrs')

        # -----
        # compute ratio anisotropy
        Rsim_obs = algo.forward_model(x, output='Rrs')
        algo.set_coef(0, 0, 0)
        Rsim_exact = algo.forward_model(x, output='Rrs')

        Rmeas_exact = Rrs_meas * Rsim_exact / Rsim_obs

        # plot results

        axs[0].plot(wl_simu, Rrs_simu, color='red', label='$retrieved$')
        axs[0].plot(wl_simu, Rrs_exact, color='grey', label='$normalized$')
        axs[0].plot(wl, Rrs_meas, color='black', ls='--', lw=0.7, marker='o', label='$data$')
        axs[0].set_ylabel('$R_{rs}\ (sr^{-1})$')
        axs[0].set_xlabel('$Wavelength\ (nm)$')
        # axs[0].text(0.98, 0.98, ds_.date.dt.strftime('%Y-%m-%d').values +
        #             '\nSZA = {:.1f} deg'.format(sza) +
        #             '\nWind Sp.={:.1f}'.format(ws) + '$m\cdot s^{-1}$' +
        #             '\nAOT(550)={:.1f}'.format(aot550) +
        #             '\nChl-a={:.1f}'.format(chl_a) + '$\mu g\cdot L^{-1}$',
        #             horizontalalignment='right',
        #             verticalalignment='top',
        #             transform=axs[0].transAxes)
        axs[0].set_title(file)
        #axs[0].legend(loc=7)
        axs[1].plot(wl_simu, Rrs_exact, color='grey', label='$normalized$')
        axs[1].plot(wl, Rmeas_exact, color='black', ls='--',lw=0.7, marker='o', label='$data$')

        # axs[1].plot(wl_simu, a_sed, '-', color='grey', lw=1, label='$a_{sed}$')
        # axs[1].plot(wl_simu, bb_sed, '--', color='grey', lw=1, label='$b_{bsed}$')
        # axs[1].plot(wl_simu, a_bg, '-', color='orange', lw=1, label='$a_{cdom}$')
        # axs[1].plot(wl_simu, a_tot, '-', color='black', lw=1, label='$a_{tot}$')
        #axs[1].set_ylabel('$IOPs\ (m^{-1})$')

        #axs[1].legend()

        # plot AERONET official correction
        axs[2].plot(wl, Rrs_aeronet_iop, color='black', ls='--', lw=0.7, marker='o', label='$data$')
        axs[2].plot(wl, Rrs_aeronet_morel, color='green', ls='--', lw=0.7, marker='o', label='$data$')



        for i in range(3):
            axs[i].minorticks_on()
            axs[i].set_xlabel('$Wavelength\ (nm)$')
        axs[0].set_xlim(380,1080)
        plt.tight_layout()

    plt.savefig(filename, dpi=300)
    plt.close()






# select the day to process
for day in range(29):
    date='2021-09-{:02}'.format(day+1)
    ds_day=ds.sel(date=date)
    if len(ds_day.date)<3:
        continue

    # ______
    # ---------------------------------
    # Set forward model parameters
    # ---------------------------------
    sza = 30
    density = 2.65
    wl = np.linspace(350, 1100, 200)
    model = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl)

    # ---------------------------------
    # Set forward model parameters
    # ---------------------------------


    i = 0
    res = []
    for name, ds_ in ds_day.groupby('date'):

        ds_ = ds_.dropna('wl')
        date = ds_.date.values

        if os.path.exists(filename):
            print("already processed")
            #continue
        # ds_ = ds.isel(date=333)
        wl = ds_.wavelength.values * 1000
        Rrs_meas = ds_[param].values  / (irr.get_F0(wl) * 0.1)
        Rrs_aeronet_iop = ds_['Lwn_IOP'].values / (irr.get_F0(wl) * 0.1)
        Rrs_aeronet_morel = ds_['Lwn_f/Q'].values / (irr.get_F0(wl) * 0.1)
        # remove deep blue
        # wl=wl[1:]
        # Rrs_meas=Rrs_meas[1:]

        sza = ds_.SZA.values
        if sza > 71.5:
            continue
        fig, axs = plt.subplots(1, 2, figsize=(18, 6), sharex=True)
        filename = opj(odir, file.replace('.', '_') + '_' +ds_.date.dt.strftime('%Y%m%d%H%M').values +'_SZA{:.1f}'.format(sza)+ '.png')
        aot550 = ds_.Aerosol_Optical_Depth.interp(wl=550).values
        ws = ds_['Wind_Speed(m/s)'].values
        chl_a = ds_["Chlorophyll-a"].values
        vza, azi = 40, 90
        wl_simu = np.linspace(350, 1100, 200)

        chl, a_cdom, S_cdom, spm_norm, fine_prop = 2, 0.5, 0.015, 2, 0.5
        nr, ni_ref, S_ni = 1.17, -0.003, 0.005
        xinit = [chl, a_cdom, S_cdom, spm_norm, fine_prop, nr, ni_ref, S_ni]  # [0.1,2,2,0.015,0.5]

        simu = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl_simu)
        simu.set_coef(sza, vza, azi)
        Rrs_simu = simu.forward_model(xinit, output='Rrs')
        algo = solver.two_modes(aphy_star, bbphy_star, sza, wl_=wl)
        algo.set_coef(sza, vza, azi)

        # perform fit
        out = algo.call_solver(Rrs_meas, xinit=xinit, max_nfev=100)
        if out.aborted:
            x = out.last_internal_values  # continue
        else:
            x = out.x

        spm_est = density * (x[3])

        # save outcomes
        res.append([date, *x, spm_est])

        # spm_est_sd = density * np.sqrt(out.covar[3,3])
        # get parameters from forward model
        Rrs_simu, a_sed, bb_sed, a_bg, bb_tot, a_tot = simu.forward_model(x, output='all')
        simu.set_coef(0, 0, 90)
        Rrs_exact = simu.forward_model(x, output='Rrs')

        # -----
        # compute ratio anisotropy
        Rsim_obs = algo.forward_model(x, output='Rrs')
        algo.set_coef(0, 0, 0)
        Rsim_exact = algo.forward_model(x, output='Rrs')

        Rmeas_exact = Rrs_meas * Rsim_exact / Rsim_obs

        # plot results

        axs[0].plot(wl_simu, Rrs_simu, color='red', label='$retrieved$')
        axs[0].plot(wl_simu, Rrs_exact, color='grey', label='$normalized$')
        axs[0].plot(wl, Rrs_meas, color='black', ls='--', lw=0.7, marker='o', label='$data$')
        axs[0].set_ylabel('$R_{rs}\ (sr^{-1})$')
        axs[0].set_xlabel('$Wavelength\ (nm)$')
        axs[0].text(0.98, 0.98, ds_.date.dt.strftime('%Y-%m-%d').values +
                    '\nSZA = {:.1f} deg'.format(sza) +
                    '\nWind Sp.={:.1f}'.format(ws) + '$m\cdot s^{-1}$' +
                    '\nAOT(550)={:.1f}'.format(aot550) +
                    '\nChl-a={:.1f}'.format(chl_a) + '$\mu g\cdot L^{-1}$',
                    horizontalalignment='right',
                    verticalalignment='top',
                    transform=axs[0].transAxes)
        axs[0].set_title(file)
        #axs[0].legend(loc=7)
        #axs[1].plot(wl_simu, Rrs_exact, color='grey', label='$normalized$')
        #axs[1].plot(wl, Rmeas_exact, color='black', ls='--',lw=0.7, marker='o', label='$data$')

        axs[1].plot(wl_simu, a_sed, '-', color='grey', lw=1, label='$a_{sed}$')
        axs[1].plot(wl_simu, bb_sed, '--', color='grey', lw=1, label='$b_{bsed}$')
        axs[1].plot(wl_simu, a_bg, '-', color='orange', lw=1, label='$a_{cdom}$')
        axs[1].plot(wl_simu, a_tot, '-', color='black', lw=1, label='$a_{tot}$')
        axs[1].set_ylabel('$IOPs\ (m^{-1})$')

        axs[1].legend()

        axs[1].text(0.96, 0.55,
                    'Chl-a = {:.2f} '.format(x[0]) + '$\mu g\cdot L^{-1}$' +
                    '\naCDOM = {:.3f} '.format(x[1]) + '$m^{-1}$' +
                    '\nSPM = {:.2f} '.format(x[3]) + '$mg\cdot L^{-1}$' +
                    '\nFine prop. = {:.2f} '.format(x[4]) +
                    '\n$n_{sed}$' + ' = {:.2f}{:.4f} '.format(x[5], x[6]),

                    bbox=dict(boxstyle="round", fc='1'), fontsize=14, horizontalalignment='right',
                    verticalalignment='top',
                    transform=axs[1].transAxes)

        for i in range(2):
            axs[i].minorticks_on()
            axs[i].set_xlabel('$Wavelength\ (nm)$')
        axs[0].set_xlim(380,1080)
        plt.tight_layout()

    plt.savefig(filename, dpi=300)
    plt.close()
