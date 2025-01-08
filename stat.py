import dash
from dash import html

dash.register_page(__name__, order = 3)

layout = html.Div([
    html.H1('This is our Stat page'),
    html.Div('This is our Stat page content.'),
])