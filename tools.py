from common import app
from dash import html, dcc
import plotly.graph_objs as go
import logging
import json

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'stream': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.ERROR},
        'file': {'class': 'logging.FileHandler',
                 'filename': 'playground.log',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    root = {
        'handlers': ['stream', 'file'],
        'level': logging.DEBUG,
        },
)

def load_page(path):
    with open(path, 'r') as _f:
        _source = _f.read()
        _example = _source

        _example = (_example
                        .replace('from common import app', '# from common import app')
                   )

        if 'import dash\n' not in _example:
            raise Exception("Didn't import dash")

        # return the layout instead of assigning it to the global app
        if 'app.layout = ' not in _example:
            raise Exception("app.layout not assigned")
        _example = _example.replace('app.layout = ', 'layout = ')

        # Remove the "# Run the server" commands
        if 'app.run_server' not in _example:
            raise Exception("app.run_server missing")
        _example = _example.replace(
            '\n    app.run_server',
            'print("Running")\n    # app.run_server'
        )
        scope = {'app': app }
        exec(_example, scope)

    return scope['layout']

def pretty_facet(name):
    return name.replace('_', ' ').title()

def get_facet_group_options(bw):
    print(bw.fields().query("type == 'character'").name)
    options = [{'label': pretty_facet(name), 'value': name} for name in 
                  bw.fields().query("type == 'character'").name if name != 'is_gov_doc']
    return options

def errorfig(txt='There was an error! We\'ve logged it and will try to fix it. Try something else!'): 
    data = [go.Heatmap(z=[0], x=[0], y=[['']], showscale=False )]
    layout = go.Layout(
        annotations = go.Annotations([
            go.Annotation(x=0, y=2,showarrow=False,
                text=txt
            ) ])
    )
    fig = go.Figure(data=data, layout=layout)
    return fig

def map_to_human_readable(df,facet):
    print("Loading JSON map")
    with open('data/map_to_human_readable.json','r') as map_to_human_readable_file:
        map_to_human_readable = json.load(map_to_human_readable_file)

    print("Applying map")
    if facet in map_to_human_readable.keys():
#        df = df.replace({ facet: map_to_human_readable[facet] })
        df = df.applymap(lambda x: map_to_human_readable[facet][x] if (type(x) is str and x in map_to_human_readable[facet]) else x)

    print("Map completed")
    return df