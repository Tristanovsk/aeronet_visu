"""
Script merging AERONET and AERONET-OC files of a given site into single CSV files.

The following files are loaded with :class:`aeronet_visu.data_loading.Read`:

* AERONET-OC (``<site>_OC.lev<lev>``),
* AERONET V3 AOD and SDA (``<site>_aod_V3.lev<lev>``, ``<site>_sda_V3.lev<lev>``),
* AERONET V3 inversions (``<site>_rin_V3.lev<lev>``, ``<site>_vol_V3.lev<lev>``).

Aerosol inversions are matched to AOD data within 5 minutes, and the resulting
aerosol data to AERONET-OC data within 35 minutes (nearest acquisition).
Outputs: ``test.csv`` (merged OC/aerosol), ``test_inv.csv``, ``test_aod.csv`` and ``test_aero.csv``.
"""

import os
import pandas as pd
from aeronet_visu import data_loading as dl

dir = '/DATA/ZIBORDI/DATA/L2h/'

levs = ("10", "15", "20")
sites = ("COVE_SEAPRISM", "Galata_Platform", "Gloria", "GOT_Seaprism", "Gustav_Dalen_Tower", "Helsinki_Lighthouse",
         "Ieodo_Station", "Lake_Erie", "LISCO", "Lucinda", "MVCO", "Palgrunden", "Socheongcho", "Thornton_C-power",
         "USC_SEAPRISM", "Venise", "WaveCIS_Site_CSI_6", "Zeebrugge-MOW1")

site = sites[-3]
lev = levs[-1]

#-------------------------
# AERONET-OC files
ifile = os.path.abspath("/DATA/AERONET/OC/" + site + "_OC.lev" + lev)
oc_df = dl.Read(ifile).read_aeronet_oc()

#-------------------------
# AERONET SDA files
ifile = os.path.abspath("/DATA/AERONET/V3/" + site + "_sda_V3.lev" + lev)
sda_df = dl.Read(ifile).read_aeronet()

#-------------------------
# AERONET AOD files
ifile = os.path.abspath("/DATA/AERONET/V3/" + site + "_aod_V3.lev" + lev)
aod_df = dl.Read(ifile).read_aeronet()

#-------------------------
# AERONET RIN files
ifile = os.path.abspath("/DATA/AERONET/V3/" + site + "_rin_V3.lev" + lev)
rin_df = dl.Read(ifile).read_aeronet_inv(skiprows=6)

#-------------------------
# AERONET VOL files
ifile = os.path.abspath("/DATA/AERONET/V3/" + site + "_vol_V3.lev" + lev)
vol_df = dl.Read(ifile).read_aeronet_inv(skiprows=6)

#-------------------------
# merge aeronet aod files
cols_to_use = sda_df.columns.difference(aod_df.columns)
df_aod = aod_df.merge(sda_df.loc[:, cols_to_use], left_index=True, right_index=True, how='outer')

#-------------------------
# merge aeronet inversion files
cols_to_use = rin_df.columns.difference(vol_df.columns)
df_inv = vol_df.merge(rin_df.loc[:, cols_to_use], left_index=True, right_index=True, how='outer')

#-------------------------
# merge aeronet aerosol files
cols_to_use = df_inv.columns.difference(df_aod.columns)
df_tot=pd.merge_asof(df_aod,df_inv.loc[:, cols_to_use], left_index=True, right_index=True,
                     tolerance=pd.Timedelta("5 minutes"), direction="nearest")

#-------------------------
# merge aeronet aerosol / oc files
df_tot['date'] = df_tot.index
oc_df['date'] = oc_df.index

dff = pd.merge_asof(oc_df, df_tot, left_index=True, right_index=True, tolerance=pd.Timedelta("35 minutes"),
                    direction="nearest")

dff.to_csv('test.csv')
df_inv.to_csv('test_inv.csv')
df_aod.to_csv('test_aod.csv')
df_tot.to_csv('test_aero.csv')