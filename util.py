import requests
import csv
import io
import geopandas as gpd
import pandas as pd
import folium
import subprocess
import os
from sqlalchemy.engine import URL
from sqlalchemy.engine import create_engine
from sqlalchemy import text
from shapely import wkt
from functools import wraps
import time


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


connection_url = URL.create(
    "mssql+pyodbc",
    username="sa",
    password="Stu@wr3r",
    host="109.222.166.90",
    port=8282,
    database="Geolocalisation",
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "TrustServerCertificate": "yes",
    },
)

engine = create_engine(connection_url)
conn = engine.connect()

@timeit
def geocode_addresses(input_list):
    df = pd.DataFrame(input_list)
    df.to_csv('adresses.txt', sep = ",")
    filename = f'adresses.txt'
    output_file = 'rich_adress.txt'

    # Input and output file paths
    filename = 'adresses.txt'
    output_file = 'rich_adress.txt'

    # Ensure the input file exists
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The input file '{filename}' does not exist.")

    # Define the curl command
    curl_command = f"""
    curl -X POST \
    -F data=@{filename} \
    -F columns=adresse \
    -F columns=commune \
    -F columns=code_postal \
    -F result_columns=latitude \
    -F result_columns=longitude \
    -F result_columns=result_type \
    -F result_columns=result_score \
    -F result_columns=result_name \
    -F result_columns=result_postcode \
    -F result_columns=result_citycode \
    -F result_columns=result_city \
    -F result_columns=result_status \
    "https://api-adresse.data.gouv.fr/search/csv/" \
    -o {output_file}
    """

    # Execute the curl command
    process = subprocess.run(curl_command, shell=True)

    # Check the process result
    if process.returncode != 0:
        raise RuntimeError(f"Curl command failed with return code {process.returncode}.")
    else:
        print(f"Output written to {output_file}")

    # Exécuter la commande curl pour chaque partie
    print("Executing command:", curl_command)
    subprocess.run(curl_command, shell=True)
    df_adress = pd.read_csv('rich_adress.txt')
    return df_adress

@timeit
def get_iris(df_adress):
    query = f"""
    SELECT CIG.code_iris
    FROM Insee.dbo.codes_iris_geometrie CIG
    WHERE CAST({df_adress.result_citycode[0]} AS VARCHAR(5)) = SUBSTRING(CIG.code_iris, 1, 5) COLLATE French_CI_AS 
    AND CIG.geography.STContains(
            geography::STPointFromText(
                'POINT(' + CAST({df_adress.longitude[0]} AS VARCHAR(20)) + ' ' + CAST({df_adress.latitude[0]} AS VARCHAR(20)) + ')', 4326
            )
        ) = 1
    AND CIG.ANNEE = 2023;
    """
    conn = engine.connect()
    trans = conn.begin() 
    df_adress['code_iris'] = conn.execute(text(query)).fetchone()
    trans.commit()  
    return df_adress

@timeit
def get_bv(df_adress):
    query = f"""
    SELECT BG.code_id_bv
    FROM 
        Elections.dbo.bureaux_geometrie BG  
    WHERE
        CAST({df_adress.result_citycode[0]} AS VARCHAR(5)) = BG.codgeo COLLATE French_CI_AS 
        AND BG.geography.STDistance(
            geography::STPointFromText(
                'POINT(' + CAST({df_adress.longitude[0]} AS VARCHAR(20)) + ' ' + CAST({df_adress.latitude[0]} AS VARCHAR(20)) + ')', 4326)
        ) > 0;
        """
    conn = engine.connect()
    trans = conn.begin()
    df_adress['code_id_bv'] = conn.execute(text(query)).fetchone()
    trans.commit()
    return df_adress

@timeit
def get_geometry(df_adress):
    # Define the parameterized query
    query = f"""
    SELECT 
        CIG.geography.STAsText() AS geometry_iris,
        CCG.geography.STAsText() AS geometry_commune,
        BG.geography.STAsText() AS geometry_bv
        
    FROM
        Insee.dbo.codes_iris_geometrie CIG,
        Insee.dbo.codes_communes_geometrie CCG,
        Elections.dbo.bureaux_geometrie BG
        
    WHERE '{df_adress.code_iris[0]}' = CIG.code_iris
    AND CIG.ANNEE = 2023
    OR CAST({df_adress.result_citycode[0]} AS VARCHAR(9)) = CCG.codgeo
    OR '{df_adress.code_id_bv[0]}' = BG.code_id_bv
        ;
    """
    df_geos = pd.read_sql_query(query, engine)
    query = f"""
    SELECT 
        nom,
        dep,
        geography.STAsText() AS geography_dpt
    FROM Insee.dbo.codes_departements_geometrie 
    WHERE CAST({df_adress.result_citycode[0]} AS VARCHAR(9)) = dep
    """
    df_dpt = pd.read_sql_query(query, engine)
    
    if df_geos.empty():
        gdf_iris = gpd.GeoDataFrame()
        gdf_commune = gpd.GeoDataFrame()
        gdf_bv = gpd.GeoDataFrame()
        return df_adress, gdf_iris, gdf_commune, gdf_bv, gdf_dpt
    
    df_adress['geometry_iris'] = df_geos['geometry_iris'].iloc[0]
    df_adress['geometry_commune'] = df_geos['geometry_commune'].iloc[0]
    df_adress['geometry_bv'] = df_geos['geometry_bv'].iloc[0]

    df_adress['geometry_iris'] = df_adress['geometry_iris'].apply(wkt.loads)
    df_adress['geometry_commune'] = df_adress['geometry_commune'].apply(wkt.loads)
    df_adress['geometry_bv'] = df_adress['geometry_bv'].apply(wkt.loads)

    # Création des GeoDataFrames pour chaque contour
    gdf_iris = gpd.GeoDataFrame(df_adress, geometry='geometry_iris', crs="EPSG:4326")
    gdf_commune = gpd.GeoDataFrame(df_adress, geometry='geometry_commune', crs="EPSG:4326")
    gdf_bv = gpd.GeoDataFrame(df_adress, geometry='geometry_bv', crs="EPSG:4326")

    gdf_iris = gdf_iris.drop(columns=['geometry_commune', 'geometry_bv'])
    gdf_commune = gdf_commune.drop(columns=['geometry_iris', 'geometry_bv'])
    gdf_bv = gdf_bv.drop(columns=['geometry_iris', 'geometry_commune'])
    
    

    # Conversion des colonnes WKT en géométries
    df_dpt['geography_dpt'] = df_dpt['geography_dpt'].apply(wkt.loads)

    # Création des GeoDataFrames pour chaque contour
    gdf_dpt = gpd.GeoDataFrame(df_dpt, geometry='geography_dpt', crs="EPSG:4326")
    gdf_dpt['geography_dpt'] = gdf_dpt['geography_dpt'].simplify(0.005)
    
    
    gdf_bv['geometry_bv'] = gdf_bv['geometry_bv'].simplify(0.005)
    gdf_iris['geometry_iris'] = gdf_iris['geometry_iris'].simplify(0.005)
    gdf_commune['geometry_commune'] = gdf_commune['geometry_commune'].simplify(0.005)
    
    
    return df_adress, gdf_iris, gdf_commune, gdf_bv, gdf_dpt

@timeit
def get_carte(df_adress, gdf_iris, gdf_commune, gdf_bv, gdf_dpt):
    carte = folium.Map(width=700, height=700, location=[df_adress['latitude'].mean(), df_adress['longitude'].mean()], zoom_start=9)

    # Ajouter des marqueurs pour chaque adresse
    for _, row in df_adress.iterrows():
        location = [row['latitude'], row['longitude']]
        texte = f"""
            <div style="font-size: 12px;">
                <b>Adresse:</b> {row['adresse']}<br>
                <b>Commune:</b> {row['commune']}
            </div>
            """
        marqueur = folium.Marker(location=location, popup=folium.Popup(texte, max_width=250), icon=folium.Icon(color="darkred", icon="info-sign"))
        marqueur.add_to(carte)

    # Ajouter la couche des contours Commune avec un contour vert plus foncé sans fond
    folium.GeoJson(
        gdf_commune,
        name="Contours Commune",
        style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'darkgreen',
            'weight': 1.5,
            'fillOpacity': 0.5 
        }
    ).add_to(carte)

    # Ajouter la couche des contours Iris avec un contour bleu clair sans fond
    folium.GeoJson(
        gdf_iris,
        name="Contours Iris",
        style_function=lambda feature: {
            'fillColor': 'lightblue',
            'color': 'blue',
            'weight': 1,
            'fillOpacity': 0.5
        }
    ).add_to(carte)

    # Ajouter la couche des contours Bureau de Vote avec un contour orange sans fond
    folium.GeoJson(
        gdf_bv,
        name="Contours Bureau de Vote",
        style_function=lambda feature: {
            'fillColor': 'orange',
            'color': 'orange',
            'weight': 1.5,
            'fillOpacity': 0.5
        }
    ).add_to(carte)

    # Ajouter la couche des contours Département avec un contour rouge sans fond
    folium.GeoJson(
        gdf_dpt,
        name="Contours Département",
        style_function=lambda feature: {
            'fillColor': 'red',
            'color': 'darkred',
            'weight': 2,
            'fillOpacity': 0  # Pas de fond
        }
    ).add_to(carte)

    # Ajouter le contrôle de couche pour afficher/masquer les contours
    folium.LayerControl().add_to(carte)
    
    return carte

if __name__ == '__main__':
    input_list = [
    {"adresse": "10 rue des Lilas", "commune": "Nantes", "code_postal": "44000"}
    ]
    out = pd.DataFrame(geocode_addresses(input_list))
    print(out)