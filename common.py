# -*- coding: utf-8 -*-
'''
A common server than can be imported, rather than indivudally initialized.
'''
import dash
import dash_bootstrap_components as dbc
import bwypy

app = dash.Dash(__name__,url_base_pathname='/app/',suppress_callback_exceptions=True,external_stylesheets=[dbc.themes.BOOTSTRAP],show_undo_redo=True)

app.css.append_css({
    "external_url" : "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/css/bootstrap.min.css"
})

graphconfig = dict(displaylogo=False,
                 modeBarButtonsToRemove=['sendDataToCloud', 'hoverCompareCartesian'])

app.index_string = """<!DOCTYPE html>
<html>
	<head>
		<!-- Global site tag (gtag.js) - Google Analytics -->
		<script async src="https://www.googletagmanager.com/gtag/js?id=G-Y6QBMH29BH"></script>
		<script>
			window.dataLayer = window.dataLayer || [];
			function gtag(){dataLayer.push(arguments);}
			gtag('js', new Date());

			gtag('config', 'G-Y6QBMH29BH');
		</script>
	</head>
</html>
"""