import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly
import plotly.graph_objs as go
from plotly import figure_factory as FF
import pandas as pd
import functools
from common import app
from common import graphconfig
from tools import get_facet_group_options, logging_config
import bwypy
import json
import logging
from logging.config import dictConfig

dictConfig(logging_config)
logger = logging.getLogger()

app.config.supress_callback_exceptions=True

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
    df.date_year = pd.to_numeric(df.date_year)
    df2 = df.query('(date_year > 1800) and (date_year < 2016)').sort_values('date_year', ascending=True)
    df2['smoothed'] = df2.TextCount.rolling(10, 0).mean()
    return df2

header = '''
# Bookworm Bar Chart
Select a field and see the raw counts in the Bookworm database
'''

controls = html.Div([
        dcc.Markdown(header),
        html.Label("Facet Group"),
        dcc.Dropdown(id='group-dropdown', options=facet_opts, value='languages'),
        html.Label("Number of results to show"),
        dcc.Slider(id='trim-slider', min=10, max=60, value=20, step=5,
                   marks={str(n): str(n) for n in range(10, 61, 10)}),
        html.Label("Ignore unknown values:", style={'padding-top': '15px'}),
        dcc.RadioItems(
            id='drop-radio',
            options=[
                {'label': u'Yes', 'value': 'drop'},
                {'label': u'No', 'value': 'keep'}
            ],
            value='drop'
        ),
        html.Label("Count by:"),
        dcc.RadioItems(id='counttype-dropdown', options=[
                {'label': u'# of Texts', 'value': 'TextCount'},
                {'label': u'# of Words', 'value': 'WordCount'}
            ], value='TextCount')
    ],
    className='col-md-3')

app.layout = html.Div([
    
    html.Div([
                controls,
                html.Div([dcc.Graph(id='bar-chart-main-graph', config=graphconfig)], className='col-md-9')
            ],
            className='row'),
    html.Div([
                html.Div([html.H2("Data"), dcc.Graph(id='bar-data-table')], id='data-table', className='col-md-5'),
                html.Div([dcc.Graph(id='date-distribution')], id='graph-wrapper', className='col-md-7')
             ],
            className='row')

], className='container-fluid')

@app.callback(
    Output('bar-chart-main-graph', 'figure'),
    [Input('group-dropdown', 'value'), Input('trim-slider', 'value'),
     Input('drop-radio', 'value'), Input('counttype-dropdown', 'value')]
)
def update_figure(group, trim_at, drop_radio, counttype):
    bw.groups = [group]
    results = get_results(group)

    df = results.frame(index=False, drop_unknowns=(drop_radio=='drop'))
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
    [Input('group-dropdown', 'value'), Input('drop-radio', 'value')]
)
def update_table(group, drop_radio):
    results = get_results(group)
    df = results.frame(index=False, drop_unknowns=(drop_radio=='drop'))
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
    [Input('bar-chart-main-graph', 'hoverData'), Input('group-dropdown', 'value')])
def print_hover_data(clickData, group):
    if clickData:
        facet_value = clickData['points'][0]['x']

        map_to_ld = {
            "genres": {
                "bibliography": "http://id.loc.gov/vocabulary/marcgt/bib",
                "government publication": "http://id.loc.gov/vocabulary/marcgt/gov",
                "fiction": "http://id.loc.gov/vocabulary/marcgt/fic",
                "biography": "http://id.loc.gov/vocabulary/marcgt/bio",
                "statistics": "http://id.loc.gov/vocabulary/marcgt/sta",
                "conference publication": "http://id.loc.gov/vocabulary/marcgt/cpb",
                "catalog": "http://id.loc.gov/vocabulary/marcgt/cat",
                "autobiography": "http://id.loc.gov/vocabulary/marcgt/aut",
                "directory": "http://id.loc.gov/vocabulary/marcgt/dir",
                "dictionary": "http://id.loc.gov/vocabulary/marcgt/dic",
                "legislation": "http://id.loc.gov/vocabulary/marcgt/leg",
                "law report or digest": "http://id.loc.gov/vocabulary/marcgt/law",
                "review": "http://id.loc.gov/vocabulary/marcgt/rev",
                "index": "http://id.loc.gov/vocabulary/marcgt/ind",
                "abstract or summary": "http://id.loc.gov/vocabulary/marcgt/abs",
                "handbook": "http://id.loc.gov/vocabulary/marcgt/han",
                "festschrift": "http://id.loc.gov/vocabulary/marcgt/fes",
                "encyclopedia": "http://id.loc.gov/vocabulary/marcgt/enc",
                "yearbook": "http://id.loc.gov/vocabulary/marcgt/yea",
                "technical report": "http://id.loc.gov/vocabulary/marcgt/ter",
                "thesis": "http://id.loc.gov/vocabulary/marcgt/the",
                "legal article": "http://id.loc.gov/vocabulary/marcgt/lea",
                "legal case and case notes": "http://id.loc.gov/vocabulary/marcgt/lec",
                "survey of literature": "http://id.loc.gov/vocabulary/marcgt/sur",
                "Songs": "http://id.loc.gov/vocabulary/marcmuscomp/sg",
                "discography": "http://id.loc.gov/vocabulary/marcgt/dis",
                "Concertos": "http://id.loc.gov/vocabulary/marcmuscomp/co",
                "Sonatas": "http://id.loc.gov/vocabulary/marcmuscomp/sn",
                "filmography": "http://id.loc.gov/vocabulary/marcgt/fil",
                "Symphonies": "http://id.loc.gov/vocabulary/marcmuscomp/sy",
                "Masses": "http://id.loc.gov/vocabulary/marcmuscomp/ms",
                "Operas": "http://id.loc.gov/vocabulary/marcmuscomp/op",
                "Other": "http://id.loc.gov/vocabulary/marcmuscomp/zz",
                "Dance forms": "http://id.loc.gov/vocabulary/marcmuscomp/df",
                "Variations": "http://id.loc.gov/vocabulary/marcmuscomp/vr",
                "Fugues": "http://id.loc.gov/vocabulary/marcmuscomp/fg",
                "Cantatas": "http://id.loc.gov/vocabulary/marcmuscomp/ct",
                "Motets": "http://id.loc.gov/vocabulary/marcmuscomp/mo",
                "Fantasias": "http://id.loc.gov/vocabulary/marcmuscomp/ft",
                "Oratorios": "http://id.loc.gov/vocabulary/marcmuscomp/or",
                "Suites": "http://id.loc.gov/vocabulary/marcmuscomp/su",
                "Preludes": "http://id.loc.gov/vocabulary/marcmuscomp/pr",
                "Overtures": "http://id.loc.gov/vocabulary/marcmuscomp/ov",
                "treaty": "http://id.loc.gov/vocabulary/marcgt/tre",
                "Marches": "http://id.loc.gov/vocabulary/marcmuscomp/mr",
                "programmed text": "http://id.loc.gov/vocabulary/marcgt/pro",
                "Divertimentos, serenades, cassations, divertissements, and notturni": "http://id.loc.gov/vocabulary/marcmuscomp/dv",
                "Rondos": "http://id.loc.gov/vocabulary/marcmuscomp/rd",
                "Periodical (MeSH)": "https://id.nlm.nih.gov/mesh/D020492",
                "Periodical (LCGFT)": "http://id.loc.gov/authorities/genreForms/gf2014026139.",
                "Requiems": "http://id.loc.gov/vocabulary/marcmuscomp/rq",
                "Canons and rounds": "http://id.loc.gov/vocabulary/marcmuscomp/cn",
                "Ballets": "http://id.loc.gov/vocabulary/marcmuscomp/bt",
                "Waltzes": "http://id.loc.gov/vocabulary/marcmuscomp/wz",
                "Folk music": "http://id.loc.gov/vocabulary/marcmuscomp/fm",
                "Madrigals": "http://id.loc.gov/vocabulary/marcmuscomp/md",
                "map": "http://id.loc.gov/vocabulary/marcgt/map",
                "Nocturnes": "http://id.loc.gov/vocabulary/marcmuscomp/nc",
                "Part-songs": "http://id.loc.gov/vocabulary/marcmuscomp/pt",
                "Hymns": "http://id.loc.gov/vocabulary/marcmuscomp/hy",
                "Passion music": "http://id.loc.gov/vocabulary/marcmuscomp/pm",
                "atlas": "http://id.loc.gov/vocabulary/marcgt/atl",
                "Minuets": "http://id.loc.gov/vocabulary/marcmuscomp/mi",
                "Toccatas": "http://id.loc.gov/vocabulary/marcmuscomp/tc",
                "Abstracts (MeSH)": "https://id.nlm.nih.gov/mesh/D020504",
                "standard or specification": "http://id.loc.gov/vocabulary/marcgt/stp",
                "Trio-sonatas": "http://id.loc.gov/vocabulary/marcmuscomp/ts",
                "Video recordings": "http://id.loc.gov/authorities/genreForms/gf2011026723",
                "Chorales": "http://id.loc.gov/vocabulary/marcmuscomp/ch",
                "Studies and exercises": "http://id.loc.gov/vocabulary/marcmuscomp/st",
                "computer program": "http://id.loc.gov/vocabulary/marcgt/com",
                "Concerti grossi": "http://id.loc.gov/vocabulary/marcmuscomp/cg",
                "Chansons, polyphonic": "http://id.loc.gov/vocabulary/marcmuscomp/cp",
                "Anthems": "http://id.loc.gov/vocabulary/marcmuscomp/an",
                "Polonaises": "http://id.loc.gov/vocabulary/marcmuscomp/po",
                "Chorale preludes": "http://id.loc.gov/vocabulary/marcmuscomp/cl",
                "videorecording": "http://id.loc.gov/vocabulary/marcgt/vid",
                "Librettos": "http://id.loc.gov/authorities/genreForms/gf2014026909",
                "Mazurkas": "http://id.loc.gov/vocabulary/marcmuscomp/mz",
                "Chant, Christian": "http://id.loc.gov/vocabulary/marcmuscomp/cc",
                "Passacaglias": "http://id.loc.gov/vocabulary/marcmuscomp/ps",
                "comic or graphic novel": "http://id.loc.gov/vocabulary/marcgt/cgn",
                "Symphonic poems": "http://id.loc.gov/vocabulary/marcmuscomp/sp",
                "numeric data": "http://id.loc.gov/vocabulary/marcgt/num",
                "Popular music": "http://id.loc.gov/vocabulary/marcmuscomp/pp",
                "Humor": "http://id.loc.gov/authorities/genreForms/gf2014026110.",
                "Canzonas": "http://id.loc.gov/vocabulary/marcmuscomp/cz",
                "Periodicals (FAST)": "http://id.worldcat.org/fast/fst01411641",
                "Pavans": "http://id.loc.gov/vocabulary/marcmuscomp/pv"
            },
            "languages": {
                "English": "eng",
                "German": "ger",
                "French": "fre",
                "Spanish": "spa",
                "Russian": "rus",
                "Chinese": "chi",
                "Japanese": "jpn",
                "Italian": "ita",
                "Portuguese": "por",
                "Latin": "lat",
                "Arabic": "ara",
                "Undetermined": "und",
                "Dutch": "dut",
                "Polish": "pol",
                "Swedish": "swe",
                "Hebrew": "heb",
                "Danish": "dan",
                "Korean": "kor",
                "Czech": "cze",
                "Hindi": "hin",
                "Indonesian": "ind",
                "Hungarian": "hun",
                "Multiple languages": "mul",
                "Norwegian": "nor",
                "Turkish": "tur",
                "Croatian": "scr",
                "No linguistic content": "zxx",
                "Urdu": "urd",
                "Thai": "tha",
                "Greek, Modern (1453-)": "gre",
                "Persian": "per",
                "Greek, Ancient (to 1453)": "grc",
                "Sanskrit": "san",
                "Tamil": "tam",
                "Ukrainian": "ukr",
                "Bulgarian": "bul",
                "Serbian": "scc",
                "Romanian": "rum",
                "Bengali": "ben",
                "Vietnamese": "vie",
                "Finnish": "fin",
                "Armenian": "arm",
                "Catalan": "cat",
                "Slovak": "slo",
                "Slovenian": "slv",
                "Yiddish": "yid",
                "Marathi": "mar",
                "Malay": "may",
                "Panjabi": "pan",
                "Afrikaans": "afr",
                "Telugu": "tel",
                "Turkish, Ottoman": "ota",
                "Tibetan": "tib",
                "Icelandic": "ice",
                "Malayalam": "mal",
                "Estonian": "est",
                "Belarusian": "bel",
                "Lithuanian": "lit",
                "Macedonian": "mac",
                "Latvian": "lav",
                "Nepali": "nep",
                "Uzbek": "uzb",
                "Welsh": "wel",
                "Kannada": "kan",
                "Georgian": "geo",
                "Gujarati": "guj",
                "Sinhalese": "snh",
                "Serbian": "srp",
                "Croatian (Discontinued Code)": "hrv",
                "Burmese": "bur",
                "Pali": "pli",
                "Kazakh": "kaz",
                "Tagalog": "tgl",
                "Azerbaijani": "aze",
                "Mongolian": "mon",
                "Javanese": "jav",
                "Irish (Discontinued Code)": "iri",
                "Hausa": "hau",
                "French, Old (ca. 842-1300)": "fro",
                "Swahili": "swa",
                "Austronesian (Other)": "map",
                "German, Middle High (ca. 1050-1500)": "gmh",
                "Syriac, Modern": "syr",
                "Rajasthani": "raj",
                "Oriya": "ori",
                "Albanian": "alb",
                "Slavic (Other)": "sla",
                "English, Middle (1100-1500)": "enm",
                "Aramaic": "arc",
                "Prakrit languages": "pra",
                "Sinhalese": "sin",
                "Church Slavic": "chu",
                "English, Old (ca. 450-1100)": "ang",
                "Irish": "gle",
                "Niger-Kordofanian (Other)": "nic",
                "Kyrgyz": "kir",
                "French, Middle (ca. 1300-1600)": "frm",
                "Altaic (Other)": "tut",
                "Romance (Other)": "roa",
                "Tagalog (Discontinued Code)": "tag",
                "Indic (Other)": "inc",
                "Tatar": "tat",
                "Mayan languages": "myn",
                "Turkmen": "tuk",
                "Sundanese": "sun",
                "Basque": "baq",
                "South American Indian (Other)": "sai",
                "Maithili": "mai",
                "Egyptian": "egy",
                "Akkadian": "akk",
                "Sino-Tibetan (Other)": "sit",
                "Quechua": "que",
                "Provençal (to 1500)": "pro",
                "Coptic": "cop",
                "Interlingua (International Auxiliary Language Association) (Discontinued Code)": "int",
                "Yoruba": "yor",
                "Papuan (Other)": "paa",
                "Braj": "bra",
                "Newari": "new",
                "Pushto": "pus",
                "Amharic": "amh",
                "Bosnian": "bos",
                "Romani": "rom",
                "Germanic (Other)": "gem",
                "Finno-Ugrian (Other)": "fiu",
                "Moldavian (Discontinued Code)": "mol",
                "Raeto-Romance": "roh",
                "Frisian (Discontinued Code)": "fri",
                "Lao": "lao",
                "Sindhi": "snd",
                "Sorbian (Other)": "wen",
                "Nahuatl": "nah",
                "Bashkir": "bak",
                "Pahlavi": "pal",
                "Assamese": "asm",
                "Galician": "glg",
                "Central American Indian (Other)": "cai",
                "Galician (Discontinued Code)": "gag",
                "Uighur": "uig",
                "Tajik": "tgk",
                "Scottish Gaelix (Discontinued Code)": "gae",
                "Khmer": "khm",
                "Esperanto (Discontinued Code)": "esp",
                "Esperanto": "epo",
                "Ethiopic": "gez",
                "Bhojpuri": "bho",
                "Scottish Gaelic": "gla",
                "Kashmiri": "kas",
                "Somali": "som",
                "North American Indian (Other)": "nai",
                "Frisian": "fry",
                "Creoles and Pidgins (Other)": "crp",
                "Zulu": "zul",
                "Tajik (Discontinued Code)": "taj",
                "Maori": "mao",
                "Ethiopic (Discontinued Code)": "eth",
                "Tahitian": "tah",
                "Miscellaneous languages": "mis",
                "Occitan (post 1500) (Discontinued Code)": "lan",
                "Hawaiian": "haw",
                "Shona": "sna",
                "Creoles and Pidgins, French-based (Other)": "cpf",
                "Caucasian (Other)": "cau",
                "Judeo-Arabic": "jrb",
                "Kurdish": "kur",
                "Sotho": "sot",
                "Awadhi": "awa",
                "Breton": "bre",
                "Occitan (post-1500)": "oci",
                "Balinese": "ban",
                "Igbo": "ibo",
                "Ladino": "lad",
                "Malagasy": "mlg",
                "German, Old High (ca. 750-1050)": "goh",
                "Tswana": "tsn",
                "Sumerian": "sux",
                "Berber (Other)": "ber",
                "Dogri": "doi",
                "Guarani (Discontinued Code)": "gua",
                "Bantu (Other)": "bnt",
                "Eskimo languages (Discontinued Code)": "esk",
                "Kinyarwanda": "kin",
                "Manipuri": "mni",
                "Xhosa": "xho",
                "Nilo-Saharan (Other)": "ssa",
                "Aymara": "aym",
                "Fula": "ful",
                "Dutch, Middle (ca. 1050-1350)": "dum",
                "Tatar (Discontinued Code)": "tar"
            },
            "digitization_agent_code": {
                "Google (google)": "google",
                "Internet Archive (ia)": "ia",
                "Library IT, Digital Library Production Service, Digital Conversion (lit-dlps-dc)": "lit-dlps-dc",
                "Cornell University (with support from Microsoft) (cornell-ms)": "cornell-ms",
                "Yale University (yale)": "yale",
                "University of California, Berkeley (berkeley)": "berkeley",
                "Getty Research Institute (getty)": "getty",
                "University of Illinois at Urbana-Champaign (uiuc)": "uiuc",
                "Texas A&M (tamu)": "tamu",
                "Cornell University (cornell)": "cornell",
                "Northwestern University (northwestern)": "northwestern",
                "Yale University (yale2)": "yale2",
                "Born Digital (placeholder) (borndigital)": "borndigital",
                "Columbia University (nnc)": "nnc",
                "Emory University (geu)": "geu",
                "Princeton University (princeton)": "princeton",
                "University of Missouri-Columbia (mou)": "mou",
                "McGill University (mcgill)": "mcgill",
                "University of Maryland (umd)": "umd",
                "Harvard University (harvard)": "harvard",
                "University of California, San Diego (ucsd)": "ucsd",
                "University of Washington (wau)": "wau",
                "American University of Beirut (aub)": "aub",
                "State University System of Florida (uf)": "uf",
                "Boston College (bc)": "bc",
                "University of California, Los Angeles (ucla)": "ucla",
                "Clark Art Institute (clark)": "clark",
                "Universidad Complutense de Madrid (ucm)": "ucm",
                "University of Pennsylvania (upenn)": "upenn",
                "National Central Library of Taiwan (chtanc)": "chtanc",
                "The University of Queensland (uq)": "uq"
            },
            "format": {
                "Text": "http://id.loc.gov/ontologies/bibframe/Text",
                "NotatedMusic": "http://id.loc.gov/ontologies/bibframe/NotatedMusic",
                "Cartography": "http://id.loc.gov/ontologies/bibframe/Cartography",
                "Text Audio": "http://id.loc.gov/ontologies/bibframe/Text http://id.loc.gov/ontologies/bibframe/Audio",
                "NotatedMusic Audio": "http://id.loc.gov/ontologies/bibframe/NotatedMusic http://id.loc.gov/ontologies/bibframe/Audio",
                "MixedMaterial": "http://id.loc.gov/ontologies/bibframe/MixedMaterial",
                "StillImage": "http://id.loc.gov/ontologies/bibframe/StillImage",
                "Audio": "http://id.loc.gov/ontologies/bibframe/Audio"
            }
        }
        logging.debug(group)
        logging.debug(facet_value)
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
