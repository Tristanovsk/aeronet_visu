Usage
=====

Installation
------------

.. code-block:: bash

   pip install .

Load AERONET / AERONET-OC data
------------------------------

The readers of :mod:`aeronet_visu.data_loading` return a :class:`pandas.DataFrame`
indexed by acquisition date, with three-level columns (parameter name, data type, wavelength in nm):

.. code-block:: python

   from aeronet_visu import data_loading as dl

   oc_df = dl.Read('Venise_OC.lev20').read_aeronet_oc()          # AERONET-OC
   aod_df = dl.Read('Venise_aod_V3.lev20').read_aeronet()        # AERONET V3 AOD / SDA
   vol_df = dl.Read('Venise_vol_V3.lev20').read_aeronet_inv()    # AERONET V3 inversions

   # water-leaving radiance spectra
   oc_df.xs('Lwn', level=1, axis=1)

Interactive visualization
-------------------------

Launch the Dash application (:mod:`aeronet_visu.visu_main`), then open http://127.0.0.1:8050 in a web browser
and upload an AERONET-OC file:

.. code-block:: python

   from aeronet_visu.visu_main import WrappedDash

   WrappedDash(debug=True)
