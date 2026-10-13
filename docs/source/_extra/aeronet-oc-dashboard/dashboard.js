/*
 * Static (client-side) version of the aeronet_visu Dash application.
 *
 * AERONET-OC Version 3 files are parsed in the browser (nothing is uploaded),
 * then displayed with plotly.js:
 *   - time series of a variable, filtered on acquisition years,
 *   - scatter plot of two variables colored by a third one,
 *   - spectra of two spectral parameters for the selected acquisitions.
 */
(function () {
  'use strict';

  const SAMPLE_FILE = 'data/Zeebrugge-MOW1_OCv3.lev15';
  const DEFAULT_N_SPECTRA = 50;
  const MAX_SPECTRA = 500;
  // columns discarded as in aeronet_visu.visu_main.list_data (+ empty/day-of-year columns)
  const EXCLUDED = /(Wave|Tri|[sS]ite|Dat|Empty|Day_of_Year|Instrument)/;

  // sequential blue ramp, light -> dark on light surface, dark -> light on dark surface
  const RAMP_LIGHT = ['#b7d3f6', '#6da7ec', '#2a78d6', '#184f95', '#0d366b'];
  const RAMP_DARK = ['#184f95', '#2a78d6', '#6da7ec', '#b7d3f6', '#cde2fb'];
  const NO_COLOR = '#898781';

  const $ = (id) => document.getElementById(id);
  const state = {data: null, selection: null, fileName: ''};

  // ------------------------------------------------------------------
  // AERONET-OC V3 reader (equivalent of data_loading.read.read_aeronet_ocv3)
  // ------------------------------------------------------------------
  function parseAeronetOC(text) {
    const lines = text.split(/\r?\n/);
    const iheader = lines.findIndex((l) => l.startsWith('AERONET_Site,'));
    if (iheader < 0) throw new Error('no "AERONET_Site,..." header line found: not an AERONET-OC Version 3 file');
    const header = lines[iheader].split(',');

    const columns = [];
    header.forEach((name, j) => {
      if (j < 3 || EXCLUDED.test(name)) return;
      const m = name.match(/^(.*)\[(\d+)nm\]$/);
      columns.push({j, name, type: m ? m[1] : null, wl: m ? Number(m[2]) : null, values: []});
    });

    const dates = [], years = [];
    let site = '';
    for (let i = iheader + 1; i < lines.length; i++) {
      const row = lines[i].split(',');
      if (row.length < 3) continue;
      const d = row[1].split(':');  // dd:mm:yyyy
      if (d.length !== 3) continue;
      site = row[0];
      dates.push(`${d[2]}-${d[1]}-${d[0]} ${row[2]}`);
      years.push(Number(d[2]));
      for (const c of columns) {
        const v = parseFloat(row[c.j]);
        c.values.push(Number.isFinite(v) && v > -998 ? v : null);
      }
    }
    if (!dates.length) throw new Error('no data rows found');

    const cols = {}, spectral = {}, names = [];
    for (const c of columns) {
      if (!c.values.some((v) => v !== null)) continue;  // drop empty columns
      cols[c.name] = c.values;
      names.push(c.name);
      if (c.type) (spectral[c.type] = spectral[c.type] || []).push({wl: c.wl, name: c.name});
    }
    for (const t of Object.keys(spectral)) {
      spectral[t].sort((a, b) => a.wl - b.wl);
      if (spectral[t].length < 2) delete spectral[t];
    }
    return {site, dates, years, cols, names, spectral, n: dates.length};
  }

  // ------------------------------------------------------------------
  // helpers
  // ------------------------------------------------------------------
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function isDark() {
    return cssVar('--surface').toLowerCase() === '#1a1a19';
  }

  function ramp() {
    return isDark() ? RAMP_DARK : RAMP_LIGHT;
  }

  function colorscale() {
    const r = ramp();
    return r.map((c, i) => [i / (r.length - 1), c]);
  }

  function hexToRgb(h) {
    const n = parseInt(h.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function colorAt(t) {
    const r = ramp();
    t = Math.min(1, Math.max(0, t)) * (r.length - 1);
    const i = Math.min(r.length - 2, Math.floor(t));
    const a = hexToRgb(r[i]), b = hexToRgb(r[i + 1]), f = t - i;
    const c = a.map((v, k) => Math.round(v + (b[k] - v) * f));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
  }

  function scaleOf(axis) {
    const checked = document.querySelector(`input[name="scale-${axis}"]:checked`);
    return checked ? checked.value : 'linear';
  }

  // color values, log10-transformed if the color scale is logarithmic
  function colorValues(name) {
    const v = state.data.cols[name];
    if (scaleOf('c') !== 'log') return v;
    return v.map((x) => (x !== null && x > 0 ? Math.log10(x) : null));
  }

  function colorTitle(name) {
    return scaleOf('c') === 'log' ? `log10(${name})` : name;
  }

  function filteredRows() {
    const y0 = Number($('year-from').value), y1 = Number($('year-to').value);
    const rows = [];
    state.data.years.forEach((y, i) => { if (y >= y0 && y <= y1) rows.push(i); });
    return rows;
  }

  function baseLayout(extra) {
    const ink2 = cssVar('--ink-2'), grid = cssVar('--grid'), axis = cssVar('--axis');
    const ax = {gridcolor: grid, linecolor: axis, zerolinecolor: axis, automargin: true};
    const layout = {
      paper_bgcolor: cssVar('--surface'),
      plot_bgcolor: cssVar('--surface'),
      font: {family: 'system-ui, sans-serif', size: 12, color: ink2},
      margin: {l: 60, r: 20, t: 10, b: 50},
      hovermode: 'closest',
      hoverlabel: {bgcolor: cssVar('--surface'), bordercolor: axis, font: {color: cssVar('--ink')}},
      dragmode: 'lasso',
      showlegend: false,
    };
    for (const k of Object.keys(extra)) {
      layout[k] = k.endsWith('axis') ? Object.assign({}, ax, extra[k]) : extra[k];
    }
    return layout;
  }

  const plotConfig = {responsive: true, displaylogo: false};

  // split rows into points with/without a valid color value
  function markerTraces(rows, x, y, c, cname, hover, showscale) {
    const ok = rows.filter((i) => x(i) !== null && y(i) !== null);
    const withC = ok.filter((i) => c[i] !== null), noC = ok.filter((i) => c[i] === null);
    const surface = cssVar('--surface');
    const traces = [];
    if (noC.length) {
      traces.push({
        type: 'scattergl', mode: 'markers', name: `no ${cname} value`,
        x: noC.map(x), y: noC.map(y), customdata: noC,
        text: noC.map((i) => hover(i)), hovertemplate: '%{text}<extra></extra>',
        marker: {size: 8, color: NO_COLOR, opacity: 0.6, line: {width: 1, color: surface}},
      });
    }
    traces.push({
      type: 'scattergl', mode: 'markers', name: cname,
      x: withC.map(x), y: withC.map(y), customdata: withC,
      text: withC.map((i) => hover(i)), hovertemplate: '%{text}<extra></extra>',
      marker: {
        size: 8, opacity: 0.85, line: {width: 1, color: surface},
        color: withC.map((i) => c[i]), colorscale: colorscale(),
        showscale, colorbar: {title: {text: colorTitle(cname), side: 'right'}, thickness: 12, outlinewidth: 0},
      },
    });
    return traces;
  }

  function fmt(v) {
    if (v === null || v === undefined) return 'n/a';
    return Math.abs(v) >= 1e4 || (Math.abs(v) < 1e-3 && v !== 0) ? v.toExponential(3) : Number(v.toPrecision(4)).toString();
  }

  // ------------------------------------------------------------------
  // figures
  // ------------------------------------------------------------------
  function drawTimeSeries(rows) {
    const d = state.data, xn = $('x-var').value, cn = $('c-var').value;
    const xv = d.cols[xn], cv = colorValues(cn), craw = d.cols[cn];
    const hover = (i) => `${d.dates[i]}<br>${xn}: ${fmt(xv[i])}<br>${cn}: ${fmt(craw[i])}`;
    const traces = markerTraces(rows, (i) => d.dates[i], (i) => xv[i], cv, cn, hover, false);
    Plotly.react('graph-time-series', traces, baseLayout({
      xaxis: {type: 'date'},
      yaxis: {title: {text: xn}, type: scaleOf('x')},
    }), plotConfig);
  }

  function drawScatter(rows) {
    const d = state.data, xn = $('x-var').value, yn = $('y-var').value, cn = $('c-var').value;
    const xv = d.cols[xn], yv = d.cols[yn], cv = colorValues(cn), craw = d.cols[cn];
    const hover = (i) => `${d.dates[i]}<br>${xn}: ${fmt(xv[i])}<br>${yn}: ${fmt(yv[i])}<br>${cn}: ${fmt(craw[i])}`;
    const traces = markerTraces(rows, (i) => xv[i], (i) => yv[i], cv, cn, hover, true);
    Plotly.react('graph-compar', traces, baseLayout({
      xaxis: {title: {text: xn}, type: scaleOf('x')},
      yaxis: {title: {text: yn}, type: scaleOf('y')},
    }), plotConfig);
  }

  function spectrumRows(rows) {
    if (state.selection) {
      const inRange = new Set(rows);
      return state.selection.filter((i) => inRange.has(i));
    }
    return rows.slice(-DEFAULT_N_SPECTRA);
  }

  function drawSpectrum(target, type, rows) {
    const d = state.data, cn = $('c-var').value, cv = colorValues(cn), craw = d.cols[cn];
    const bands = d.spectral[type] || [];
    rows = rows.slice(-MAX_SPECTRA);
    const cs = rows.map((i) => cv[i]).filter((v) => v !== null);
    const cmin = Math.min(...cs), cmax = Math.max(...cs);
    const traces = [];
    for (const i of rows) {
      const pts = bands.filter((b) => d.cols[b.name][i] !== null);
      if (pts.length < 2) continue;
      const c = cv[i] === null ? NO_COLOR : colorAt(cmax > cmin ? (cv[i] - cmin) / (cmax - cmin) : 0.5);
      traces.push({
        type: 'scatter', mode: 'lines+markers',
        x: pts.map((b) => b.wl), y: pts.map((b) => d.cols[b.name][i]),
        line: {color: c, width: 2}, marker: {color: c, size: 6},
        opacity: 0.85,
        hovertemplate: `${d.dates[i]}<br>%{x} nm: %{y:.4g}<br>${cn}: ${fmt(craw[i])}<extra></extra>`,
      });
    }
    if (cs.length) {
      // invisible trace carrying the colorbar
      traces.push({
        type: 'scatter', mode: 'markers', x: [null], y: [null], hoverinfo: 'skip',
        marker: {
          color: [cmin], cmin, cmax: cmax > cmin ? cmax : cmin + 1, colorscale: colorscale(), showscale: true,
          colorbar: {title: {text: colorTitle(cn), side: 'right'}, thickness: 12, outlinewidth: 0},
        },
      });
    }
    Plotly.react(target, traces, baseLayout({
      xaxis: {title: {text: 'Wavelength (nm)'}},
      yaxis: {title: {text: type}},
      dragmode: 'zoom',
    }), plotConfig);
    return traces.length - (cs.length ? 1 : 0);
  }

  function drawSpectra(rows) {
    const srows = spectrumRows(rows);
    const n = drawSpectrum('spectrum1-graph', $('spectrum1').value, srows);
    drawSpectrum('spectrum2-graph', $('spectrum2').value, srows);
    const what = state.selection
      ? `${srows.length} selected acquisition(s)`
      : `the ${srows.length} most recent acquisitions of the selected years — select points on the time series or scatter plot to choose others (double-click to reset)`;
    const cut = srows.length > MAX_SPECTRA ? ` (only the last ${MAX_SPECTRA} are drawn)` : '';
    $('selection-info').textContent = `Spectra: ${what}${cut}; ${n} spectra drawn.`;
  }

  function drawAll() {
    if (!state.data) return;
    const rows = filteredRows();
    drawTimeSeries(rows);
    drawScatter(rows);
    drawSpectra(rows);
  }

  // ------------------------------------------------------------------
  // controls
  // ------------------------------------------------------------------
  function fillSelect(sel, groups, value) {
    sel.innerHTML = '';
    for (const [label, names] of groups) {
      const parent = label ? document.createElement('optgroup') : sel;
      if (label) { parent.label = label; sel.appendChild(parent); }
      for (const n of names) parent.appendChild(new Option(n, n));
    }
    sel.value = value;
  }

  function variableGroups(d) {
    const scalars = d.names.filter((n) => !/\[\d+nm\]$/.test(n));
    const groups = [['Parameters', scalars]];
    for (const t of Object.keys(d.spectral)) groups.push([t, d.spectral[t].map((b) => b.name)]);
    return groups;
  }

  // band of a spectral type closest to a wavelength (falls back on the first variable)
  function closest(d, type, wl) {
    const bands = d.spectral[type];
    if (!bands) return d.names[0];
    return bands.reduce((a, b) => (Math.abs(b.wl - wl) < Math.abs(a.wl - wl) ? b : a)).name;
  }

  function keep(sel, d, fallback) {
    return sel.value && d.cols[sel.value] ? sel.value : fallback;
  }

  function setupControls(d) {
    const years = [...new Set(d.years)].sort();
    for (const id of ['year-from', 'year-to']) {
      fillSelect($(id), [[null, years.map(String)]], String(id === 'year-from' ? years[0] : years[years.length - 1]));
    }
    const groups = variableGroups(d);
    const lwn = d.spectral['Lwn_f/Q'] ? 'Lwn_f/Q' : 'Lwn';
    const cdefault = d.cols['Chlorophyll-a'] ? 'Chlorophyll-a' : closest(d, 'Aerosol_Optical_Depth', 870);
    fillSelect($('x-var'), groups, keep($('x-var'), d, closest(d, lwn, 550)));
    fillSelect($('y-var'), groups, keep($('y-var'), d, closest(d, lwn, 670)));
    fillSelect($('c-var'), groups, keep($('c-var'), d, cdefault));

    const types = Object.keys(d.spectral);
    const pick = (sel, pref) => (d.spectral[sel.value] ? sel.value : types.find((t) => t === pref) || types[0]);
    const s1 = pick($('spectrum1'), lwn), s2 = pick($('spectrum2'), 'Aerosol_Optical_Depth');
    fillSelect($('spectrum1'), [[null, types]], s1);
    fillSelect($('spectrum2'), [[null, types]], s2);
  }

  function buildScaleRadios() {
    document.querySelectorAll('.scale').forEach((div) => {
      const axis = div.dataset.for;
      for (const [label, value] of [['Linear', 'linear'], ['Log', 'log']]) {
        const l = document.createElement('label');
        const r = document.createElement('input');
        r.type = 'radio'; r.name = `scale-${axis}`; r.value = value; r.checked = value === 'linear';
        r.addEventListener('change', drawAll);
        l.append(r, label);
        div.appendChild(l);
      }
    });
  }

  function onSelected(ev) {
    if (!ev || !ev.points) return;
    const idx = ev.points.map((p) => p.data.customdata[p.pointIndex]);
    state.selection = [...new Set(idx)].sort((a, b) => a - b);
    drawSpectra(filteredRows());
  }

  function onDeselect() {
    state.selection = null;
    drawSpectra(filteredRows());
  }

  // ------------------------------------------------------------------
  // data loading
  // ------------------------------------------------------------------
  function load(text, fileName) {
    try {
      const d = parseAeronetOC(text);
      state.data = d;
      state.selection = null;
      state.fileName = fileName;
      setupControls(d);
      $('status').textContent =
        `${d.site} — ${d.n} acquisitions from ${d.dates[0].slice(0, 10)} to ${d.dates[d.n - 1].slice(0, 10)} (${fileName})`;
      drawAll();
    } catch (e) {
      $('status').textContent = `${fileName}: file format not appropriate (${e.message}).`;
    }
  }

  function readFile(file) {
    if (!file) return;
    $('status').textContent = `Reading ${file.name}…`;
    const reader = new FileReader();
    reader.onload = () => load(reader.result, file.name);
    reader.readAsText(file);
  }

  function loadSample() {
    $('status').textContent = 'Loading sample data…';
    fetch(SAMPLE_FILE)
      .then((r) => { if (!r.ok) throw new Error(r.statusText); return r.text(); })
      .then((t) => load(t, SAMPLE_FILE.split('/').pop()))
      .catch(() => {
        $('status').textContent = 'Sample data could not be loaded (page opened from disk?): upload an AERONET-OC file.';
      });
  }

  // follow the light/dark theme of the documentation page when embedded
  function syncThemeWithParent() {
    let root;
    try {
      if (window.parent === window) return;
      root = window.parent.document.documentElement;
    } catch (e) {
      return;
    }
    const apply = () => {
      const t = root.dataset.theme;
      if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
      else delete document.documentElement.dataset.theme;
      drawAll();
    };
    new MutationObserver(apply).observe(root, {attributes: true, attributeFilter: ['data-theme']});
    apply();
  }

  function init() {
    buildScaleRadios();
    for (const id of ['year-from', 'year-to', 'x-var', 'y-var', 'c-var']) $(id).addEventListener('change', drawAll);
    for (const id of ['spectrum1', 'spectrum2']) $(id).addEventListener('change', () => drawSpectra(filteredRows()));
    for (const id of ['graph-time-series', 'graph-compar']) {
      const el = $(id);
      Plotly.newPlot(el, [], baseLayout({}), plotConfig);
      el.on('plotly_selected', onSelected);
      el.on('plotly_deselect', onDeselect);
    }

    $('file-input').addEventListener('change', (e) => readFile(e.target.files[0]));
    const zone = $('drop-zone');
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('over'));
    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('over');
      readFile(e.dataTransfer.files[0]);
    });
    $('sample-btn').addEventListener('click', loadSample);
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', drawAll);

    // report the page height so that the documentation can size its iframe
    if (window.parent !== window && window.ResizeObserver) {
      new ResizeObserver(() => {
        window.parent.postMessage({aeronetDashboardHeight: Math.ceil(document.body.getBoundingClientRect().height)}, '*');
      }).observe(document.body);
    }

    syncThemeWithParent();
    loadSample();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
