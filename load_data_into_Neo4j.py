import requests
from neo4j import GraphDatabase

# Configurar la conexión a Neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "neo4j"

driver = GraphDatabase.driver(uri, auth=(username, password))

# Lista de nombres de clusters fijos y sus categorías correspondientes
clusters = [
{"name": "historical", "categories": ["historical_places", "historic_districts", "historic_sites"]},
{"name": "industrial/urban", "categories": ["abandoned_mineshafts", "farms", "power_stations"]},
{"name": "beaches", "categories": ["golden_sand_beaches", "white_sand_beaches", "urban_beaches"]},
{"name": "natural", "categories": ["geological_formations", "caves", "volcanoes", "rock_formations"]},
{"name": "religion", "categories": ["churches", "other_churches", "eastern_orthodox_churches"]},
{"name": "sport", "categories": ["stadiums", "sport"]},
{"name": "tourist_facilities", "categories": ["banks", "railway_stations", "tourist_facilities"]},
{"name": "foods", "categories": ["restaurants", "fast_food", "bakeries", "fish_stores", "pubs"]},
{"name": "shops", "categories": ["shops", "supermarkets"]},
{"name": "archeology", "categories": ["moveable_bridges", "viaducts", "bridges", "suspension_bridges"]},
{"name": "accommodations", "categories": ["hostels", "guest_houses", "hotels", "villas_and_cottages"]},
{"name": "amusement", "categories": ["casinos", "fountains", "nightclubs", "amusement_parks"]}
]


# Crear nodos de los clusters fijos
with driver.session() as session:
    for cluster in clusters:
        cluster_name = cluster['name']
        session.run("CREATE (:Cluster {name: $name})", name=cluster_name)


# Obtener los datos de las ciudades desde Geonames
geonames_url = "http://api.geonames.org/searchJSON?q=&country=ES&adminCode1=&maxRows=1000&username=pslasso&featureClass=P"
response = requests.get(geonames_url)
data = response.json()

# Crear los nodos de las ciudades en Neo4j
with driver.session() as session:
    for city in data['geonames']:
        city_name = city['name']
        city_lat = float(city['lat'])
        city_lng = float(city['lng'])

        # Verificar si la ciudad ya existe en la base de datos
        result = session.run("MATCH (city:City {name: $name}) RETURN city", name=city_name)
        if result.single() is not None:
            print(f"La ciudad {city_name} ya existe en la base de datos. No se creará un nuevo nodo.")
            continue

        session.run("CREATE (:City {name: $name, latitude: $lat, longitude: $lng})", name=city_name, lat=city_lat, lng=city_lng)

        if city_name != "Madrid":
            continue

        # Obtener los datos de los lugares de interés para cada ciudad
        opentripmap_url = f"https://api.opentripmap.com/0.1/en/places/radius?radius=5000&lon={city_lng}&lat={city_lat}&apikey=5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced"
        response = requests.get(opentripmap_url)
        data = response.json()

        # Comprobar si la respuesta contiene los datos esperados
        if 'features' in data and len(data['features']) > 0:
            for feature in data['features']:
                place_id = feature['properties']['xid']

                # Obtener los datos del lugar de interés utilizando el place_id
                place_info_url = f"https://api.opentripmap.com/0.1/en/places/xid/{place_id}?apikey=5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced"
                response = requests.get(place_info_url)
                place_info = response.json()

                if 'name' not in place_info:
                    print(f"Datos incompletos para el lugar de interés en la ciudad {city_name}: {place_info}")
                    continue

                place_name = place_info['name']
                kinds = place_info.get('kinds', "").split(',')
                # print(f"kinds:{kinds}")

                # Crear el nodo del lugar de interés
                session.run("MERGE (place:Place {name: $place_name})", place_name=place_name)

                # Crear las relaciones con los clusters correspondientes
                for cluster in clusters:
                    if any(category.lower() in place_name.lower() for category in cluster['categories']):
                        session.run("""
                            MATCH (place:Place {name: $place_name})
                            MATCH (cluster:Cluster {name: $cluster_name})
                            MERGE (place)-[:BELONGS_TO]->(cluster)
                        """, place_name=place_name, cluster_name=cluster['name'])

        else:
            print(f"No se encontraron lugares de interés para la ciudad {city_name}.")


# Cerrar la conexión a Neo4j
driver.close()
