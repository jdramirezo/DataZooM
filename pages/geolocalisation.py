import dash
import folium
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
dash.register_page(__name__, order = 2)

description_product = dbc.Container(
            dbc.Card(
                dbc.CardBody(
                    dcc.Markdown("""
                                # Type your own adress 🚀

                                Description for the first product
                                
                                """),
                    className="p-4",  # Padding for all sides
                ),
                className="mt-4 mb-4 shadow",  # Margins for the card and shadow for better visuals
            ),
    fluid=True,  # Full-width container
)

import dash_bootstrap_components as dbc

geo_container = dbc.Container(
    dbc.Col(
        [
            dbc.Card(
                [
                    #Adresse, commune et code postale
                    dbc.CardHeader("Saisie d'adresse"),
                    dbc.CardBody(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("Adresse"), 
                                    dbc.Input(placeholder="Adresse", id = "in_add"),
                                ],
                                className="mb-3",
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.Input(placeholder="Commune", id = "in_comm"),
                                    dbc.InputGroupText("Commune"),
                                ],
                                className="mb-3",
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.Input(placeholder="Code postale", id = "in_cp"),
                                    dbc.InputGroupText("Code postale"),
                                ],
                                className="mb-3",
                            ),
                        ]
                    ),
                ]
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button("Vérifier l'adresse", id = "b1", n_clicks=0),
                    dbc.Button("Envoyer", id = "e1", n_clicks=0),
                    dbc.Button("Éffacer", id = "e2", n_clicks=0),
                ]
            ),      
        ]
    )
)

map_center = [47.218371, -1.553621]  # Coordinates for Nantes, France
folium_map = folium.Map(location=map_center, zoom_start=13)
folium.Marker(location=map_center, popup="Nantes Center").add_to(folium_map)

# Save the Folium map as an HTML string
map_path = "map.html"
folium_map.save(map_path)


map_container = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Map View"),
                dbc.CardBody([
                    html.Iframe(
                        id="map", 
                        srcDoc=open(map_path, "r").read(),
                        width="100%",
                        height="500",
                    )
                ])
            ])
        ])
    ])
], fluid=True)

layout = html.Div([
    description_product, 
    geo_container,
    map_container,
    html.Div('This is our Geo page content.'),
    dcc.Store(id='intermediate-value-geo')
])
