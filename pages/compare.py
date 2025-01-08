import dash
from dash import html

dash.register_page(__name__, order = 4)

layout = html.Div([
    html.H1('This is our Compare page'),
    html.Div('This is our Home Compare content.'),
])