import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, order = 1)

layout = html.Div([
    dbc.Container(
            dbc.Card(
                dbc.CardBody(
                    dcc.Markdown("""
                                # Welcome to DataZoom 🚀

                                DataZoom is a data-oriented company that aims to harness the prower of OpenData for our clients
                                
                                
                                """),
                    className="p-4",  # Padding for all sides
                ),
                className="mt-4 mb-4 shadow",  # Margins for the card and shadow for better visuals
            ),
    fluid=True,  # Full-width container
    )
])