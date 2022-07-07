import dash
from dash import dcc, html
from dash.dependencies import State, Input, Output
import dash_bootstrap_components as dbc
import plotly
import plotly.graph_objs as go
from plotly import figure_factory as FF
import pandas as pd
import functools
from common import app
from common import graphconfig
from tools import get_facet_group_options, logging_config, map_to_human_readable
import bwypy
import json
import logging
from logging.config import dictConfig

dictConfig(logging_config)
logger = logging.getLogger()

with open('config.json','r') as options_file:
    bwypy_options = json.load(options_file)

bwypy.set_options(database=bwypy_options['settings']['dbname'], endpoint=bwypy_options['settings']['endpoint'])
bw = bwypy.BWQuery(verify_fields=False,verify_cert=False)

facet_opts = get_facet_group_options(bw)

# This will cache identical calls
@functools.lru_cache(maxsize=32)
def get_results(group):
    bw.counttype = ['WordCount', 'TextCount']
    bw.groups = ['*'+group]
    bw.search_limits = { group + '__id' : {"$lt": 60 } }
    return bw.run()

bw_date = bwypy.BWQuery(verify_fields=False,verify_cert=False)

@functools.lru_cache(maxsize=32)
def get_date_distribution(group, facet):
    bw_date.groups = ['date_year']
    bw_date.counttype = ['TextCount']
    bw_date.search_limits = { group: facet }
    results = bw_date.run()
    df = results.frame(index=False)
    logging.debug("Got date distribution")
    logging.debug(df)
    try:
        df = map_to_human_readable(df,group)
        logging.debug("Ran map to human readable")
        logging.debug(df)
    except Exception as e:
        logging.error("ERROR with date distribution")
        logging.error(e)
    df.date_year = pd.to_numeric(df.date_year)
    logging.debug("Converted dates to numeric")
    df2 = df.query('(date_year > 1800) and (date_year < 2016)').sort_values('date_year', ascending=True)
    df2['smoothed'] = df2.TextCount.rolling(10, 0).mean()
    return df2

header = '''
# Bookworm Bar Chart
Select a field and see the raw counts in the Bookworm database
'''

controls = html.Div([
        dcc.Markdown(header),
        html.Label("Facet Group", className='mb-2'),
        dcc.Dropdown(id='bar-group-dropdown', options=facet_opts, value='languages', disabled=False),
        html.Label("Number of results to show", className='mb-2'),
        dcc.Slider(id='trim-slider', min=10, max=60, value=20, step=5,
                   marks={str(n): str(n) for n in range(10, 61, 10)}, className='py-0 px-0'),
        html.Label("Ignore unknown values:", className='mb-2 pt-3'),
        dcc.RadioItems(
            id='drop-radio',
            options=[
                {'label': u'Yes', 'value': 'drop'},
                {'label': u'No', 'value': 'keep'}
            ],
            value='drop',
            labelClassName='mb-2'
        ),
        html.Label("Count by:", className='mb-2'),
        dcc.RadioItems(id='counttype-dropdown', options=[
                {'label': u'# of Texts', 'value': 'TextCount'},
                {'label': u'# of Words', 'value': 'WordCount'}
            ], value='TextCount', labelClassName='mb-2')
    ],
    className='col-md-3 px-3')

app.layout = html.Div([
    
    html.Div([
                controls,
                html.Div([dcc.Graph(id='bar-chart-main-graph', config=graphconfig)], className='col-md-9 px-3')
            ],
            className='row'),
    html.Div([
                html.Div([html.H2("Data"), dcc.Graph(id='bar-data-table')], id='data-table', className='col-md-5 px-3'),
                html.Div([dcc.Graph(id='date-distribution')], id='graph-wrapper', className='col-md-7 px-3')
             ],
            className='row')

], className='container-fluid')

#def show_processing(facet,figure):
@app.callback(
    Output('bar-group-dropdown', 'disabled'),
    Input('bar-group-dropdown', 'value'),
#    Input('bar-chart-main-graph', 'figure'),
#    Input('bar-data-table', 'figure')
)
def show_processing(facet):#, chart, table):
#    logging.debug(dash.callback_context)
#    logging.debug("Show Processing")
#    return False
    logging.debug("Show Processing")
    logging.debug(dash.callback_context.triggered)
    for element in dash.callback_context.triggered:
        logging.debug(element['prop_id'])
    context = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
#    if len(context) > 0:
#        return True
#    else:
#        return False

    if context == 'bar-group-dropdown' or len(context) == 0:
        logging.debug(context)
        return False
    else:
        logging.debug(context)
        return True
#    if context == 'bar-chart-main-graph':
#        return False
#    else:
#        return True

@app.callback(
    Output('bar-chart-main-graph', 'figure'),
    Input('bar-group-dropdown', 'value'),
    Input('trim-slider', 'value'),
    Input('drop-radio', 'value'),
    Input('counttype-dropdown', 'value')
)
def update_figure(group, trim_at, drop_radio, counttype):
    bw.groups = [group]
    logging.debug("Groups:")
    logging.debug(bw.groups)
    results = get_results(group)
    logging.debug("Results for new figure:")
    logging.debug(results)

    df = results.frame(index=False, drop_unknowns=(drop_radio=='drop'))
    logging.debug("Created DataFrame of results")
    logging.debug(df)
    try:
        df = map_to_human_readable(df,group)
        logging.debug("Ran map to human readable")
    except Exception as e:
        logging.error("ERROR occured!")
        logging.error(e)
    df = df.copy()
    df_trimmed = df.head(trim_at)
        
    data = [
        go.Bar(
            x=df_trimmed[group],
            y=df_trimmed[counttype]
        )
    ]
    
    return {
            'data': data,
            'layout': {
                'yTitle': counttype,
                'title': group.replace('_', ' ').title()
            }
        }

@app.callback(
    Output('bar-data-table', 'figure'),
    Input('bar-group-dropdown', 'value'),
    Input('drop-radio', 'value')
)
def update_table(group, drop_radio):
    results = get_results(group)
    df = results.frame(index=False, drop_unknowns=(drop_radio=='drop'))
    logging.debug("Updated table")
    logging.debug(df)
    df = map_to_human_readable(df,group)
    df = df.copy()
    return FF.create_table(df)
    #return html.Table(
        # Header
        #[html.Tr([html.Th(col) for col in df.columns])] +
        # Body
        #[html.Tr([
        #            html.Td(df.iloc[i][col]) for col in df.columns
        #        ]) for i in range(min(len(df), 100))]
    #)

@app.callback(
    Output('date-distribution', 'figure'),
    Input('bar-chart-main-graph', 'hoverData'),
    State('bar-group-dropdown', 'value')
)
def print_hover_data(clickData, group):
    if clickData:
        facet_value = clickData['points'][0]['x']

        with open('data/map_to_ld.json','r') as map_to_ld_file:
            map_to_ld = json.load(map_to_ld_file)

        if group in map_to_ld:
            df = get_date_distribution(group, map_to_ld[group][facet_value])
        else:
            df = get_date_distribution(group, facet_value)
        df = df.copy()
        data = [
            go.Scatter(
                x=df['date_year'],
                y=df['smoothed']
            )
        ]
        return {
            'data': data,
            'layout': {
                'height': 300,
                'yaxis': {'range': [0, int(df.smoothed.max())+100]},
                'title': 'Date Distribution for ' + facet_value.replace('_', ' ').title()
            }
        }
    else:
        data = [
            go.Scatter(
                x=list(range(1800, 2016)),
                y=[0]*(2013-1800)
            )
        ]
        return {
            'data': data,
            'layout': {
                'height': 300,
                'yaxis': {'range': [0, 100000]},
                'title': 'Select a ' + group.replace('_', ' ') + ' to see date distribution'            }
        }
    
if __name__ == '__main__':
    # app.scripts.config.serve_locally = False
    app.config.supress_callback_exceptions = True
    app.run_server(debug=True, port=10012, threaded=True, host='0.0.0.0')
