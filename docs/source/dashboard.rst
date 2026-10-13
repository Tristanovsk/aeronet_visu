AERONET-OC dashboard
====================

Interactive overview of AERONET-OC Version 3 data. It is a static (browser-only) version of the
Dash application of :mod:`aeronet_visu.visu_main`: files are read in your browser and are not uploaded anywhere.

* Drag and drop (or select) an AERONET-OC V3 file downloaded from the
  `AERONET-OC website <https://aeronet.gsfc.nasa.gov/new_web/ocean_color.html>`_
  (e.g., ``<site>_OCv3.lev15`` or ``<site>_OCv3.lev20``).
  A sample file from the Zeebrugge-MOW1 site (level 1.5) is displayed by default.
* Filter the acquisitions by year, choose the variables of the time series, the scatter plot and the color scale.
* Select acquisitions with the box or lasso tool on the time series or scatter plot to display their spectra.

`Open the dashboard in full page <aeronet-oc-dashboard/index.html>`_

.. raw:: html

   <iframe id="aeronet-oc-dashboard-frame" src="aeronet-oc-dashboard/index.html" title="AERONET-OC dashboard"
           style="width: 100%; height: 2200px; border: 0;" loading="lazy"></iframe>
   <script>
     window.addEventListener('message', function (e) {
       var h = e.data && e.data.aeronetDashboardHeight;
       if (h) document.getElementById('aeronet-oc-dashboard-frame').style.height = (h + 20) + 'px';
     });
   </script>

.. note::

   AERONET-OC data are distributed by the International AERONET Federation. As stated in the header of the
   data files, their use requires offering co-authorship to the Principal Investigator (PI) of the site.
