import os
import pandas as pd
import numpy as np
import flask
import json
import base64
import datetime
import io
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import matplotlib as mpl
from textwrap import dedent as d

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dte
from datetime import datetime
from flask_caching import Cache

import re


# import aeronet
# from config import *
def matplotlib_to_plotly(cmap, pl_entries):
    h = 1.0 / (pl_entries - 1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = map(np.uint8, np.array(cmap(k * h)[:3]) * 255)
        pl_colorscale.append([k * h, 'rgb' + str((C[0], C[1], C[2]))])

    return pl_colorscale


cmap = mpl.cm.Spectral
colorscale = matplotlib_to_plotly(cmap, 25)
# import data_loading
#
# # dff = df.xs(site,level='site')
# dir = '/DATA/ZIBORDI/DATA/L2h/'
#
# levs = ("10", "15", "20")
# sites = ("COVE_SEAPRISM", "Galata_Platform", "Gloria", "GOT_Seaprism", "Gustav_Dalen_Tower", "Helsinki_Lighthouse",
#          "Ieodo_Station", "Lake_Erie", "LISCO", "Lucinda", "MVCO", "Palgrunden", "Socheongcho", "Thornton_C-power",
#          "USC_SEAPRISM", "Venise", "WaveCIS_Site_CSI_6", "Zeebrugge-MOW1")
#
# site = sites[-3]
# lev = levs[-1]
# file = dir + site + '_l' + lev + '_solvo.csv'
# # df = pd.read_csv(file, header=[0, 1, 2], index_col=0, parse_dates=True)
# # df.columns.set_levels(pd.to_numeric(df.columns.levels[2], errors='coerce'), level=2, inplace=True)
# # df.sort_index(axis=1, level=2, sort_remaining=False, inplace=True)
# #
# # dff = df
# # available_data = dff.columns.levels[0]
# # available_data = available_data.drop(filter(lambda s: re.match('.*(Wave|Tri|[sS]ite|Dat)', s), available_data))
# # available_site = [site]
# # year = dff.index.year
# df = pd.read_csv(file)
# set default colors
# plotly.colors.DEFAULT_PLOTLY_COLORS=['rgb(166,206,227)', 'rgb(31,120,180)', 'rgb(178,223,138)', 'rgb(51,160,44)', 'rgb(251,154,153)', 'rgb(227,26,28)']
year = pd.Series([2016, 2017])
available_data = ['']
dff = pd.DataFrame()

app = dash.Dash()
# app.css.append_css('data/aeronet_layout.css')
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache'
})

# ------------------------------------------------------
# layout section
# ------------------------------------------------------

app.layout = html.Div([
    html.Div([
        html.H1(
            'AERONET - Data Overview',
            className='eight columns',
            style={

                'display': 'inline-block'}
        ),
        html.Img(
            src='https://photos-6.dropbox.com/t/2/AADMqc6n7fvvGpRTeXlHq0P-0ZbLqjbhGDQldYQCPzFQ5w/12/534523458/png/32x32/1/_/1/2/solvo.png/EJiUqaMEGOKbFiACKAI/70FuinUO8GnOi9LDgolkaXAeQ_z35_S5MdhLUN4p1Xw?preserve_transparency=1&size=2048x1536&size_mode=3',
            className='one columns',
            alt='solvo',
            style={
                # 'height': '100',
                # 'width': '225',
                'float': 'right',
                'display': 'inline-block',
            },
        ),
    ],
        className='row'
    ),

    html.Div([
        #   file selection box
        html.Div([
            html.H4('File selection:', id='filename'),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '80%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
                multiple=False
            )
        ],
            style={'margin-top': '0',
                   'width': '35%', 'display': 'inline-block',
                   }),
    ]),

    # Time range selection
    html.Div(
        [
            html.H4('Filter by acquisition date:'),  # noqa: E501
            dcc.RangeSlider(
                id='year-slider',

            ),
        ],
        style={'margin-top': '0',
               'width': '65%',
               'display': 'inline-block',
               }
    ),

    html.Div(
        [
            html.H4(
                '',
                id='year-text',
                className='four columns',
                style={'text-align': 'right', 'margin-top': '0'}
            ),
        ]),

    html.Div([

        html.Div([

            html.H4('Time series variable (x-axis on scatter plot):'),
            html.Div([
                dcc.Dropdown(
                    id='xaxis-column')
            ],
                style={'width': '85%'}
            ),
            html.Div([
                dcc.RadioItems(
                    id='xaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                    value='Linear',
                    labelStyle={'display': 'inline-block'}
                )
            ],
                style={'width': '36%',
                       'margin-top': '0',
                       # 'margin-left': '26%'
                       'display': 'inline-block',
                       }),
        ],
            style={'width': '28%',
                   'margin-top': '0',
                   # 'margin-left': '26%'
                   'display': 'inline-block',
                   }),

        html.Div([

            html.H4('Scatter plot y-axis variable:'),
            dcc.Dropdown(
                id='yaxis-column',

            ),
            dcc.RadioItems(
                id='yaxis-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block'}
            )
        ],
            style={'width': '22%',
                   'margin-top': '0',
                   'display': 'inline-block',
                   'margin-left': '6%'}),

        html.Div([

            html.H4('Color variable:'),
            dcc.Dropdown(
                id='color-column',
            ),
            dcc.RadioItems(
                id='color-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block'})
        ],
            style={'width': '22%',
                   'margin-top': '0',
                   'display': 'inline-block',
                   'margin-left': '6%'}),
    ], ),
    # Time series and comparison graphs
    html.Div([
        html.Div([
            dcc.Graph(id='graph-time-series')],
            # className='eight columns',
            style={'width': '60.8%',
                   'margin-top': '20',
                   'display': 'inline-block',

                   }),
        html.Div([
            dcc.Graph(id='graph-compar')],
            # className='four columns',
            style={'width': '39%',
                   'margin-top': '20',
                   'float': 'right',
                   'display': 'inline-block'
                   })
    ]),
    # Spectrum graphs
    html.Div([
        html.Div([
            dcc.Graph(id='spectrum-graph')],
            # className='eight columns',
            style={'width': '49.9%',
                   'margin-top': '0',
                   'display': 'inline-block',

                   }),
        html.Div([
            dcc.Graph(id='spectrum2-graph')],
            # className='eight columns',
            style={'width': '49.9%',
                   'float': 'right',
                   'display': 'inline-block',

                   }),
    ],

        # style={'display': 'inline-block'},
        # className='row'
    ),

    html.Div([

        html.H4('Spectral parameter 1'),
        dcc.Dropdown(
            id='spectrum1',
            value='Lwn_solvo2'),
    ],
        style={'width': '48.9%',
               'float': 'left', }),

    html.Div([

        html.H4('Spectral parameter 2'),
        dcc.Dropdown(
            id='spectrum2',
            value='Lwn'),
    ],
        style={'width': '48.9%',
               'float': 'right', }),

    html.Div([
        dcc.Markdown(d("""
                **Selection Data**

                Choose the lasso or rectangle tool in the graph's menu
                bar and then select points in the graph.
            """)),
        # html.Pre(id='selected-data', style=styles['pre']),
    ], className='three columns'),

    # hidden signal value
    html.Div(id='dataset', style={'display': 'none'}),
],

    style={
        'width': '90%',
        'fontFamily': 'Sans-Serif',
        'margin-left': 'auto',
        'margin-right': 'auto'})


# ------------------------------------------------------
# function section
# ------------------------------------------------------
def filter_dataframe(df, year_slider):
    df = df[(df.index.year >= year_slider[0])
            & (df.index.year <= year_slider[1])]
    return df


def parse_contents(contents, year):
    global df
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=[0, 1, 2], index_col=0, parse_dates=True)
        df.columns.set_levels(pd.to_numeric(df.columns.levels[2], errors='coerce').fillna(''), level=2, inplace=True)
        df.sort_index(axis=1, level=2, sort_remaining=False, inplace=True)
    except Exception as e:
        print(e)
        print('File format not appropriate.')
        return

    return filter_dataframe(df, year)


def list_data(contents, level=0):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=[0, 1, 2], index_col=0, nrows=0, parse_dates=True)
    c = df.columns.levels[level]
    # remove useless variables
    c = c.drop(filter(lambda s: re.match('.*(Wave|Tri|[sS]ite|Dat)', s), c))
    return [{'label': i, 'value': i} for i in c]


def get_index(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=[0, 1, 2], index_col=0, parse_dates=True)
    return df.index


def figure_spectrum(chosen, column_name, selected_data, color_column_name):
    dff = df.loc[(chosen), :]
    parameters = df.loc[(chosen), (color_column_name)].values
    dff = dff.loc[:, (slice(None), [column_name, 'std', 'wavelength'])]
    dff.columns = dff.columns.droplevel()
    dff = dff.stack(level=['l2'])
    norm = mpl.colors.Normalize(vmin=np.min(parameters), vmax=np.max(parameters))
    # create a ScalarMappable and initialize a data structure
    s_m = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    s_m.set_array([])
    i = 0
    trace = []
    for date, x in dff.groupby(level=0):
        trace.append(go.Scatter(
            x=x['wavelength'].values.flatten(),  # spectrum,
            y=x[column_name].values.flatten(),
            text=x.index.get_level_values(0),
            mode='lines+markers',
            marker={
                'size': 12,
                'opacity': 0.5,
                'color': 'rgba({}, {}, {}, {})'.format(*s_m.to_rgba(parameters[i]).flatten()),
                # x.unique(),#color': df.index.get_level_values(0),
                'line': {'width': 0.5, 'color': 'white'},
            },
            line=go.Line(color='rgba({}, {}, {}, {})'.format(*s_m.to_rgba(parameters[i]).flatten()), width=2),
            showlegend=False
        ))
        i = i + 1

    # spectrum = df[label['aod']].stack()
    return {
        'data': trace,
        'layout': go.Layout(
            xaxis={
                'title': 'Wavelength (nm)',

            },
            yaxis={
                'title': column_name,

            },
            margin={'l': 50, 'b': 40, 't': 20, 'r': 50},
            hovermode='closest',

            height=500,
            font=dict(color='#CCCCCC'),
            titlefont=dict(color='#CCCCCC', size='14'),

            plot_bgcolor="#191A1A",
            paper_bgcolor="#020202",
        )
    }


# ------------------------------------------------------
# callback section
# ------------------------------------------------------
# ---------------------------
# update uploaded data
@app.callback(Output('dataset', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def update_output(contents, filename):
    print filename
    return contents


@app.callback(Output('filename', 'children'),
              [Input('upload-data', 'filename')])
def show_filename(filename):
    return 'File selection: ' + str(filename)


# ---------------------------
# update dropdown menus
@app.callback(Output('xaxis-column', 'options'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)


@app.callback(Output('yaxis-column', 'options'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)


@app.callback(Output('color-column', 'options'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)


@app.callback(Output('spectrum1', 'options'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents, level=1)


@app.callback(Output('spectrum2', 'options'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents, level=1)


@app.callback(Output('xaxis-column', 'value'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)[0]


@app.callback(Output('yaxis-column', 'value'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)[1]


@app.callback(Output('color-column', 'value'),
              [Input('dataset', 'children')])
def update_dropdown(contents):
    return list_data(contents)[2]


# ---------------------------
# time range selection
@app.callback(Output('year-slider', 'min'),
              [Input('dataset', 'children')])
def update_slider(contents):
    year = get_index(contents).year
    return year.min() - 1


@app.callback(Output('year-slider', 'max'),
              [Input('dataset', 'children')])
def update_slider(contents):
    year = get_index(contents).year
    return year.max()


@app.callback(Output('year-slider', 'value'),
              [Input('dataset', 'children')])
def update_slider(contents):
    year = get_index(contents).year
    return [year.max() - 1, year.max()]


@app.callback(Output('year-slider', 'marks'),
              [Input('dataset', 'children')])
def update_slider(contents):
    year = get_index(contents).year
    return {str(y): str(y) for y in year.unique()}


# Slider -> year text
@app.callback(Output('year-text', 'children'),
              [Input('year-slider', 'value')])
def update_year_text(year_slider):
    return "{} | {}".format(year_slider[0], year_slider[1])


# time series graphs
@app.callback(
    Output('graph-time-series', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('xaxis-type', 'value'),
     Input('color-column', 'value'),
     Input('year-slider', 'value'),
     Input('dataset', 'children')])
def update_graph(xaxis_column_name,
                 xaxis_type,
                 color_column_name,
                 year_value, value):
    df = parse_contents(value, year_value)
    dff = df
    # print df.index, df.loc[:, (xaxis_column_name, slice(None))].values
    if xaxis_type == 'Log':
        dff[dff <= 0] = np.nan

    return {
        'data': [go.Scattergl(
            x=dff.index,  # [df['Indicator Name'] == xaxis_column_name]['Value'],
            y=dff.loc[:, (xaxis_column_name, slice(None))].values.flatten(),
            # .xs(xaxis_column_name,level=0,axis=1), #.values,
            # text=df[df['Indicator Name'] == yaxis_column_name]['Country Name'],
            mode='markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'color': df.loc[:, (color_column_name, slice(None))].values.flatten(),
                'line': {'width': 0.5, 'color': 'white'},
                'colorscale': colorscale},

        )],
        'layout': go.Layout(
            xaxis={
                'title': '',
            },
            yaxis={
                'title': xaxis_column_name,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },

            height=500,
            margin={'l': 50, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest',
            font=dict(color='#CCCCCC'),
            titlefont=dict(color='#CCCCCC', size='14'),

            plot_bgcolor="#191A1A",
            paper_bgcolor="#020202",
        )
    }


# compar graphs
@app.callback(
    Output('graph-compar', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('xaxis-type', 'value'),
     Input('yaxis-column', 'value'),
     Input('yaxis-type', 'value'),
     Input('color-column', 'value'),
     Input('year-slider', 'value'),
     Input('dataset', 'children'),
     Input('graph-time-series', 'selectedData')])
def update_graph(xaxis_column_name, xaxis_type,
                 yaxis_column_name, yaxis_type,
                 color_column_name,
                 year_value,
                 value, chosen):
    df = parse_contents(value, year_value)
    dff = df
    if 'Log' in [xaxis_type, yaxis_type]:
        # TODO separate x and y axis to keep negative values on linear axis
        dff[dff <= 0] = np.nan

    return {
        'data': [go.Scattergl(
            x=dff.loc[:, (xaxis_column_name, slice(None))].values.flatten(),
            y=dff.loc[:, (yaxis_column_name, slice(None))].values.flatten(),
            text=dff.index,
            mode='markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'color': dff.loc[:, (color_column_name, slice(None))].values.flatten(),
                'line': {'width': 0.5, 'color': 'white'},
                'showscale': True,
                'colorscale': colorscale
            },

        )],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },
            yaxis={
                'title': yaxis_column_name,
                'type': 'linear' if yaxis_type == 'Linear' else 'log'
            },
            margin={'l': 50, 'b': 40, 't': 20, 'r': 50},
            hovermode='closest',

            height=500,
            font=dict(color='#CCCCCC'),
            titlefont=dict(color='#CCCCCC', size='14'),

            plot_bgcolor="#191A1A",
            paper_bgcolor="#020202",
        )
    }


# selection from time series graph -> spectrum graph
@app.callback(Output('spectrum-graph', 'figure'),
              [Input('spectrum1', 'value'),
               Input('graph-time-series', 'selectedData'),
               Input('color-column', 'value'),
               Input('dataset', 'children')])
def spectrum_figure(column_name, selected_data, color_column_name, value):
    if selected_data is None:
        selected_data = {'points': [{'x': df.index[-50:-1]}]}
        chosen = [pd.to_datetime(point['x'], unit='ms') for point in selected_data['points']][0]
    else:
        chosen = [pd.to_datetime(point['x'], unit='ms') for point in selected_data['points']]
    return figure_spectrum(chosen, column_name, selected_data, color_column_name)


# selection from time series graph -> spectrum graph
@app.callback(Output('spectrum2-graph', 'figure'),
              [Input('spectrum2', 'value'),
               Input('graph-time-series', 'selectedData'),
               Input('color-column', 'value'),
               Input('dataset', 'children')])
def spectrum_figure(column_name, selected_data, color_column_name, value):
    if selected_data is None:
        selected_data = {'points': [{'x': df.index[-50:-1]}]}
        chosen = [pd.to_datetime(point['x'], unit='ms') for point in selected_data['points']][0]
    else:
        chosen = [pd.to_datetime(point['x'], unit='ms') for point in selected_data['points']]
    # df = parse_contents(value, year_value)
    return figure_spectrum(chosen, column_name, selected_data, color_column_name)


app.run_server()
