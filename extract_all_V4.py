import pandas as pd
import requests
import os
import sqlite3

directorio = os.path.dirname(os.path.abspath(__file__))
cities_csv = os.path.join(directorio, "cities.csv")
db_file = os.path.join(directorio, "travel.db")

# Base de datos
conn = sqlite3.connect(db_file)
c = conn.cursor()

# Tablas en la base de datos si existieran por haber hecho algún test
#c.execute("DROP TABLE IF EXISTS cities")
#c.execute("DROP TABLE IF EXISTS places")


# Tablas en la base de datos
c.execute('''CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                lon FLOAT,
                lat FLOAT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY,
                city_id INTEGER,
                name TEXT,
                xid TEXT,
                lon FLOAT,
                lat FLOAT,
                rate TEXT,
                wikidata TEXT,
                kinds TEXT,
                otm TEXT,
                wikipedia TEXT,
                image TEXT,
                image_height INTEGER,
                image_width INTEGER,
                description TEXT,
                FOREIGN KEY (city_id) REFERENCES cities(id)
            )''')

# API key de OpenTripMap
api_key = "5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced"

def get_place_info(place_id):
    response = requests.get(f"https://api.opentripmap.com/0.1/en/places/xid/{place_id}?apikey={api_key}")
    data = response.json()
    return data

def save_place_info(city_id, place_info):
    c.execute('''INSERT INTO places (
                    city_id,
                    name,
                    xid,
                    lon,
                    lat,
                    rate,
                    wikidata,
                    kinds,
                    otm,
                    wikipedia,
                    image,
                    image_height,
                    image_width,
                    description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (
                  city_id,
                  place_info.get('name',''),
                  place_info.get('xid',''),
                  place_info.get('point', {}).get('lon',''),
                  place_info.get('point', {}).get('lat',''),
                  place_info.get('rate',''),
                  place_info.get('wikidata',''),
                  place_info.get('kinds',''),
                  place_info.get('otm',''),
                  place_info.get('wikipedia',''),
                  place_info.get('preview', {}).get('source',''), # source image
                  place_info.get('preview', {}).get('height',''),
                  place_info.get('preview', {}).get('width',''),
                  place_info.get('wikipedia_extracts', {}).get('text','')
              )
              )
    conn.commit()


# Lectura de ciudades desde el archivo cities.csv
df = pd.read_csv(cities_csv)

for _, row in df.iterrows():
    name = row['City']
    lon = row['Lon']
    lat = row['Lat']

    # Verificar si la ciudad ya existe en la tabla "cities"
    c.execute("SELECT id FROM cities WHERE name=?", (name,))
    existing_row = c.fetchone()

    if existing_row is None:
        # Guardar datos de la ciudad en la tabla 'cities'
        c.execute("INSERT INTO cities (name, lon, lat) VALUES (?, ?, ?)", (name, lon, lat))
        conn.commit()
        city_id = c.lastrowid

        # Obtener lugares cercanos de OpenTripMap
        response = requests.get(f"https://api.opentripmap.com/0.1/en/places/radius?radius=1000&lon={lon}&lat={lat}&apikey={api_key}")
        data = response.json()

        if 'features' in data and len(data['features']) > 0:
            for feature in data['features']:
                place_id = feature['properties']['xid']
                place_info = get_place_info(place_id)
                save_place_info(city_id, place_info)

    else:
        print(f"La ciudad '{name}' ya existe en la tabla 'cities'.")
