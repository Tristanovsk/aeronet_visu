import os
import pandas as pd
import numpy as np
import matplotlib as mpl
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
file = 'Lake_Okeechobee_N_OCv3.lev20'
#file = 'Venise_OCv3.lev20'
odir = opj('/DATA/AERONET/OCv3_invRrs/fig/phyco', file.replace('.', '_'))
if not os.path.exists(odir):
    os.makedirs(odir)

irr = dl.Irradiance()
irr.load_F0()

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

# ======================
# IOP_star for algae data
# =====================
chl_models = ['Bricaud1995', 'Ciotti2002_Sf005', 'Ciotti2002_Sf01',
              'Ciotti2002_Sf02', 'Ciotti2002_Sf03', 'Ciotti2002_Sf033',
              'Ciotti2002_Sf05', 'Gernez_Mesodinium']

aphy_star, bbphy_star = u.data().load_iop_phyto(chl_models[4])

# ______
# ---------------------------------
# Set forward model parameters
# ---------------------------------
sza = 30
density = 2.65
wl = np.linspace(350, 1100, 200)
model = solver.phyco(aphy_star, bbphy_star, sza, wl_=wl)

# ---------------------------------
# Set forward model parameters
# ---------------------------------
for name, ds_ in ds.groupby('date'):
    print(name)
    filename = opj(odir, file.replace('.', '_') + '_' + ds_.date.dt.strftime('%Y%m%d%H%M').values + '.png')
    if os.path.exists(filename):
        print("already processed")
        continue
    #ds_ = ds.isel(date=333)
    wl = ds_.wavelength.values * 1000
    Rrs_meas = ds_[param].values / (irr.get_F0(wl) * 0.1)
    # remove deep blue
    # wl=wl[1:]
    # Rrs_meas=Rrs_meas[1:]

    sza = ds_.SZA.values
    aot550= ds_.Aerosol_Optical_Depth.interp(wl=550).values
    ws = ds_['Wind_Speed(m/s)'].values
    chl_a = ds_["Chlorophyll-a"].values
    vza, azi = 40, 90
    wl_simu = np.linspace(350, 1100, 200)

    chl, PC, a_cdom, S_cdom, spm_norm, fine_prop = 2,0., 0.5, 0.015, 2, 0.5
    nr, ni_ref, S_ni = 1.17, -0.003, 0.005
    xinit = [chl, PC, a_cdom, S_cdom, spm_norm, fine_prop, nr, ni_ref, S_ni]  # [0.1,2,2,0.015,0.5]


    simu = solver.phyco(aphy_star, bbphy_star, sza, wl_=wl_simu)
    simu.set_coef(sza, vza, azi)
    Rrs_simu = simu.forward_model(xinit, output='Rrs')
    algo = solver.phyco(aphy_star, bbphy_star, sza, wl_=wl)
    algo.set_coef(sza, vza, azi)

    # perform fit
    out = algo.call_solver(Rrs_meas, xinit=xinit, max_nfev=100)
    if out.aborted:
        x = out.last_internal_values  # continue
    else:
        x = out.x

    spm_est = density * (x[3])
    # spm_est_sd = density * np.sqrt(out.covar[3,3])
    # get parameters from forward model
    Rrs_simu, a_sed, bb_sed, a_bg, bb_tot, a_tot = simu.forward_model(x, output='all')
    simu.set_coef(0, 0, 90)
    Rrs_exact = simu.forward_model(x, output='Rrs')

    # plot results
    fig, axs = plt.subplots(1, 2, figsize=(18, 6), sharex=True)

    axs[0].plot(wl, Rrs_meas, color='black', ls='--', marker='o', label='$data$')
    axs[0].plot(wl_simu, Rrs_simu, color='red', label='$retrieved$')
    axs[0].plot(wl_simu, Rrs_exact, color='grey', label='$normalized$')

    axs[0].set_ylabel('$R_{rs}\ (sr^{-1})$')
    axs[0].set_xlabel('$Wavelength\ (nm)$')
    axs[0].text(0.98, 0.98, ds_.date.dt.strftime('%Y-%m-%d').values +
                '\nSZA = {:.1f} deg'.format(sza)+
                '\nWind Sp.={:.1f}'.format(ws)+'$m\cdot s^{-1}$'+
                '\nAOT(550)={:.1f}'.format(aot550)+
                '\nChl-a={:.1f}'.format(chl_a)+'$\mu g\cdot L^{-1}$',
                horizontalalignment='right',
                verticalalignment='top',
                transform=axs[0].transAxes)
    axs[0].set_title(file)
    axs[0].legend(loc=7)

    axs[1].plot(wl_simu, a_sed, '-', color='grey', lw=1, label='$a_{sed}$')
    axs[1].plot(wl_simu, bb_sed, '--', color='grey', lw=1, label='$b_{bsed}$')
    axs[1].plot(wl_simu, a_bg, '-', color='orange', lw=1, label='$a_{cdom}$')
    axs[1].plot(wl_simu, a_tot, '-', color='black', lw=1, label='$a_{tot}$')
    axs[1].set_ylabel('$IOPs\ (m^{-1})$')
    axs[1].set_xlabel('$Wavelength\ (nm)$')
    axs[1].legend()

    axs[1].text(0.96, 0.55,
                'Chl-a = {:.2f} '.format(x[0]) + '$\mu g\cdot L^{-1}$' +
                '\nPC = {:.2f} '.format(x[1]) + '$\mu g\cdot L^{-1}$' +
                '\naCDOM = {:.3f} '.format(x[2]) + '$m^{-1}$'+
                '\nSPM = {:.2f} '.format(x[4]) + '$mg\cdot L^{-1}$' +
                '\nFine prop. = {:.2f} '.format(x[5]) +
                '\n$n_{sed}$'+' = {:.2f}{:.4f} '.format(x[6],x[7]),

                bbox=dict(boxstyle="round", fc='1'), fontsize=14, horizontalalignment='right',
                verticalalignment='top',
                transform=axs[1].transAxes)
    plt.tight_layout()

    plt.savefig(filename, dpi=300)
    plt.close()
