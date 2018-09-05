# Generic python stuff
import bson.json_util as json_util
from collections import deque
import time

# UI/Dash stuff
import dash
from dash.dependencies import Input, Output, Event
import dash_core_components as dcc
import dash_html_components as html

import plotly
import plotly.figure_factory as ff
import plotly.graph_objs as go

# DS
import pandas as pd

# Numerical stuff
import random

# Local stuff
from utils.database import DB, FileDB, MongoDB

#######################
# Data Analysis / Model
#######################
max_length = 40
db = DB()

def retrieve_obd_values():
    global db
    df = None

    if isinstance(db, FileDB):
        with open(db.get_file(collection='weather')) as f:
            d = deque(f.readlines(), maxlen=max_length)
        l = [json_util.loads(d[i])['data'] for i in range(len(d))]
        # build a dataframe now
        lindex = [i['date'] for i in l]
        ldata = [dict([(i,j) for i,j in el.items() if i != 'date']) for el in l]
        df = pd.DataFrame(ldata, index=lindex)

    if df is not None:
        # Only keep data from the last 24 hours before latest measurment
        latest = df.loc[df.index==df.index.max()]
        ts = latest.index[0]
        ts = ts - pd.Timedelta(days=1)
        df = df.loc[df.index>ts]
    return df

#########################
# Dashboard Layout / View
#########################

# Common definitions
colors = {
    'background': '#F6F8FD', #clear grey or dark grey with #111111
    'text': '#7FDBFF'
}
default_style={} #{'backgroundColor': colors['background']}
default_title_style={'textAlign': 'center',
                     'color': colors['text']}

# Set up Dashboard and create layout
app = dash.Dash('')
df = retrieve_obd_values()

# Define weather tab
div_weather = html.Div(
    id='div_weather',
    children = [
        html.Div(
            style=default_style,
            children=[
                html.H2(style=default_title_style,
                        children='Weather Monitoring',
                ),
            ]
        ),
        dcc.Dropdown(id='weather_data_name',
                     options=[{'label': s, 'value': s}
                              for s in df.keys()],
                     value=['ambient_temp_C', 'rain_sensor_temp_C',
                            'wind_speed_KPH'],
                     multi=True
                     ),
        html.Div(children=html.Div(id='weather_graphs'), className='row'),
        dcc.Interval(
            id='weather_update',
            interval=1*1000, # in milliseconds
            n_intervals=0)
    ],
)

# Define observatory tab
div_observatory = html.Div(
    id='div_observatory',
    style=default_style,
    children = [
        html.H2(style=default_title_style,
                children='Observatory Building',
        ),
        html.Div(
            children = [
                html.H4(children='Observatory table'),
                html.Div(id='observatory_tables'),
            ]),
        dcc.Interval(
            id='observatory_update',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ]
)

# Define telescope tab
div_telescope = html.Div(
    id='div_telescope',
    style=default_style,
    children = [
        html.H2(style=default_title_style,
                children='Telescope Monitoring',
        ),
    ]
)

# Now define main Div
app.layout = html.Div(
    className="container", # goesalong with some external css
    style={'width':'98%','margin-left':1,'margin-right':1,'max-width':50000},
    children=[
        html.Div(style=default_style, children=[
            html.H1(style=default_title_style, children=
                    'Observatory Monitoring Dashboard',
            ),
        ]),
        dcc.Tabs(id="tabs", value='tab1', children=[
            dcc.Tab(label='Weather monitoring', value='tab1'),
            dcc.Tab(label='Observatory monitoring', value='tab2'),
            dcc.Tab(label='Telescope monitoring', value='tab3'),
        ]),
        div_weather,
        div_observatory,
        div_telescope
    ]
)

# list of callback for each tab
@app.callback(Output('div_weather', 'style'),
              [Input('tabs', 'value')])
def update_div_weather_visible(tab_val):
    if tab_val == 'tab1':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div_observatory', 'style'),
              [Input('tabs', 'value')])
def update_div_weather_visible(tab_val):
    if tab_val == 'tab2':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div_telescope', 'style'),
              [Input('tabs', 'value')])
def update_div_weather_visible(tab_val):
    if tab_val == 'tab3':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


###########################################################
# Interaction Between Components / Controller : Weather tab
###########################################################


@app.callback(
    Output('weather_graphs','children'),
    [Input('weather_data_name', 'value')],
    events=[Event('weather_update', 'interval')]
    )
def update_graph(data_names):
    graphs = []
    df = retrieve_obd_values()
    if data_names is None:
        return graphs

    if len(data_names)>2:
        class_choice = 'col s12 m6 l4'
    elif len(data_names) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'

    for data_name in data_names:
        data = go.Scatter(
            x=list(df.index),
            y=list(df[data_name]),
            name='Scatter',
            mode = 'lines',
            #color="#6897bb"
        )

        graphs.append(html.Div(dcc.Graph(
            id=data_name,
            animate=False, #True messes with autorange
            figure={'data': [data],'layout' :
                go.Layout(xaxis=dict(#range=[df.index.min(),
                                     #       df.index.max()],
                                     autorange=True,
                                     showgrid=True,
                                     zeroline=False,
                                     showline=False,
                                     showticklabels=True),
                          yaxis=dict(#range=[df[data_name].min(),
                                     #       df[data_name].max()],
                                     autorange=True,
                                     showgrid=True,
                                     zeroline=False,
                                     showline=True,
                                     showticklabels=True),
                          margin={'l':50,'r':50,'t':45,'b':45},
                          title='{}'.format(data_name)),}
            ), className=class_choice))

    return graphs

###############################################################
# Interaction Between Components / Controller : Observatory tab
###############################################################

@app.callback(
    Output('observatory_tables', 'children'),
    events=[Event('observatory_update', 'interval')])    
def table_update():
    df = pd.DataFrame([{'a':1,'b':2},{'a':44,'b':88}], index=['1st','2nd'])
    return dcc.Graph(
        id='observatory_sensor_table',
        figure=ff.create_table(df, index=True))



#############################################################
# Interaction Between Components / Controller : Telescope tab
#############################################################

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})

if __name__ == '__main__':
    #app.css.config.serve_locally = True
    #app.scripts.config.serve_locally = True
    app.run_server(debug=True)

