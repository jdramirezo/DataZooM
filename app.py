import dash
import re
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from util import geocode_addresses, get_iris, get_bv, get_geometry, get_carte
app = dash.Dash()

app = Dash(__name__, use_pages=True)

upbar = dbc.Container(
    [
        # First Row: Logo and Title
        dbc.Row(
            [
                dbc.Col(
                    html.Img(src="assets/logo.png", alt="Logo", style={"height": "100px"}),
                    width="auto",  # Adjust width for the logo
                ),
                dbc.Col(
                    html.H1("DataZooM", className="text-center"),
                    className="d-flex align-items-center justify-content-center",
                ),
            ],
            className="justify-content-center mb-4",
        ),
        # Second Row: Centered Navbar
        dbc.Row(
            dbc.Nav(
                [
                    dbc.NavLink(
                                html.Div(page["name"], className="ms-2"),
                                href=page["path"],
                                active="exact",
                            )
                            for page in dash.page_registry.values()
                ],
                pills=True,
                ),
            className="justify-content-center",
        ),
    ],
    fluid=True,
)

app.layout = html.Div([
    upbar,
    dash.page_container
])

@app.callback(
    Output("intermediate-value-geo", "data"),   # Update the intermediate store
    Input("e1", "n_clicks"),                    # Triggered by button click
    State("in_add", "value"),                   # Get current input value
    State("in_comm", "value"),                  # Get current input value
    State("in_cp", "value"),                    # Get current input value
    State("intermediate-value-geo", "data"),                # Get current store data
)
def update_store(n_clicks, in_add, in_comm, in_cp, current_data):
    if n_clicks > 0 and in_add and in_comm and in_cp:
        input_list = [{"adresse": f'{in_add}', "commune": f'{in_comm}', "code_postal": f'{in_cp}'}]
        geo_list = geocode_addresses(input_list)
        return geo_list.to_json(orient='split')
    return current_data 

@app.callback(Output('map', 'srcDoc'), Input('intermediate-value-geo', 'data'))
def update_graph(e_data):
    if not e_data:
        return open("map.html", "r").read()
    else:
        df_adress = pd.read_json(e_data,  orient='split')
        df_adress['result_postcode'] = df_adress['result_postcode'].astype(str).apply(lambda x: '0' + x if re.match(r'^\d{4}\.0$', str(x)) else x)
        df_adress['result_postcode'] = df_adress['result_postcode'].astype(str).str.replace('.0', '').str.zfill(5)
        df_adress['result_citycode'] = df_adress['result_citycode'].astype(str).str.replace('.0', '').str.zfill(5)
        df_adress = get_iris(df_adress)
        df_adress = get_bv(df_adress)
        df_adress, gdf_iris, gdf_commune, gdf_bv, gdf_dpt = get_geometry(df_adress)
        carte = get_carte(df_adress, gdf_iris, gdf_commune, gdf_bv, gdf_dpt)
        updated_map = carte  # Example: Paris
        updated_map.save("updated_map.html")
        return open("updated_map.html", "r").read()
    

if __name__ == '__main__':
    app.run(debug=True)