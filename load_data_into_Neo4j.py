from math import radians, sin, cos, sqrt, atan2
import requests
from neo4j import GraphDatabase

# Neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "aleneo4j"

driver = GraphDatabase.driver(uri, auth=(username, password))

# Lista de nombres de clusters fijos y sus categorías correspondientes
clusters = [
    {'name': 'Museums', 'categories': [
        'history_museums',
        'museums',
        'archaeology',
        'biographical_museums',
        'museums_of_science_and_technology',
        'fashion_museums',
        'other_museums',
        'maritime_museums',
        'military_museums',
        'science_museums',
        'local_museums',
        'railway_museums',
        'art_galleries'
    ]},
    {'name': 'Theaters', 'categories': [
        'theatres_and_entertainments',
        'concert_halls',
        'opera_houses',
        'other_theatres',
        'music_venus'
    ]},
    {'name': 'Historical', 'categories': [
        'historic_settlements',
        'historic_districts',
        'historic_architecture',
        'historic_house_museums',
        'historic_object',
        'historical_places',
        'historic_fortifications',
        'historic_battlefields',
        'war_memorials',
        'scultures',
        'archaeological_sites',
        'rune_stones'
    ]},
    {'name': 'Industrial/Urban', 'categories': [
        'industrial_facilities',
        'power_stations',
        'factories',
        'urban_environment',
        'abandoned_mineshafts',
        'farms',
        'transmitter_towers',
        'water_towers',
        'bell_towers',
        'skyscrapers',
        'other_buildings',
        'clock_towers',
        'mills'
    ]},
    {'name': 'Beaches', 'categories': [
        'black_sand_beaches',
        'white_sand_beaches',
        'beaches',
        'rocks_beaches',
        'nude_beaches',
        'shingle_beaches',
        'golden_sand_beaches',
        'beaches'
    ]},
    {'name': 'Natural', 'categories': [
        'natural_monuments',
        'rock_formations',
        'natural_springs',
        'springs_others',
        'nature_reserves',
        'geological_formations',
        'volcanoes',
        'caves',
        'waterfalls',
        'lagoons',
        'dry_lakes',
        'rivers',
        'water',
        'nature_reserves',
        'mountain_peaks',
        'canyons',
        'other_nature_conservation_areas',
        'natural'
    ]},
    {'name': 'Religion', 'categories': [
        'buddhist_temples',
        'religion'
        'synagogues',
        'churches',
        'eastern_orthodox_churches',
        'cathedrals',
        'mosques',
        'catholic_churches',
        'hindu_temples',
        'other_churches',
        'monasteries',
        'minarets'
    ]},
    {'name': 'Sport', 'categories': [
        'sport',
        'stadiums'
    ]},
    {'name': 'Tourist facilities', 'categories': [
        'tourist_facilities',
        'tourist_object',
        'visitor_centers',
        'accommodations',
        'guest_houses',
        'hostels',
        'apartments',
        'campsites',
        'hotels',
        'other_hotels'
    ]},
    {'name': 'Foods', 'categories': [
        'foods',
        'fish_stores',
        'restaurants',
        'fast_food',
        'cafes',
        'bakeries',
        'wineries',
        'biergartens',
        'bars'
    ]},
    {'name': 'Shops', 'categories': [
        'shops',
        'malls',
        'marketplaces',
        'supermarkets'
    ]},
    {'name': 'Archeology', 'categories': [
        'archaeology',
        'archaeological_sites',
        'dolmens',
        'cave_paintings',
        'moveable_bridges',
        'viaducts',
        'bridges',
        'suspension_bridges',
        'roman_bridges',
        'footbridges',
        'stone_bridges',
        'hillforts',
        'other_bridges',
        'aqueducts',
        'canals',
        'roman_villas',
        'cave_paintings',
        'crypts',
        'towers',
        'tumuluses',
        'neocropolises',
        'menhirs',
        'mausoleums',
        'amphiteatres',
        'castles',
        'megaliths',
        'fortifications',
        'triumphal_archs',
        'fortified_towers',
        'watch_towers'
    ]},
    {'name': 'Accommodations', 'categories': [
        'accommodations',
        'guest_houses',
        'hostels',
        'apartments',
        'campsites',
        'hotels',
        'other_hotels'
    ]},
    {'name': 'Amusement', 'categories': [
        'amusement_parks',
        'casinos',
        'nightclubs',
        'amusements',
        'water_parks',
        'zoos',
        'cinemas',
        'planetariums',
        'view_points',
        'dams',
        'saunas',
        'amusements',
        'hot',
        'aquariums',
        'pools'
    ]}
]

# Calculating geodesic distances
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # radius Earth km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


# Fixed clusters nodes
with driver.session() as session:
    for cluster in clusters:
        cluster_name = cluster['name']
        session.run("CREATE (:Cluster {name: $name})", name=cluster_name)


# Obtaining cities from Geonames
geonames_url = "http://api.geonames.org/searchJSON?q=&country=ES&adminCode1=&maxRows=1000&username=pslasso&featureClass=P"
response = requests.get(geonames_url)
data = response.json()

# Creating nodes for cities in Neo4j
with driver.session() as session:
    for city in data['geonames']:
        city_name = city['name']
        city_lat = float(city['lat'])
        city_lng = float(city['lng'])

        # Check if the city already exists in Neo4j
        result = session.run("MATCH (city:City {name: $name}) RETURN city", name=city_name)
        if result.single() is not None:
            print(f"La ciudad {city_name} ya existe en la base de datos. No se creará un nuevo nodo.")
            continue

        session.run("CREATE (:City {name: $name, latitude: $lat, longitude: $lng})", name=city_name, lat=city_lat, lng=city_lng)

        #if city_name != "Madrid":
        #    continue

        # Obtaining places for the current city
        opentripmap_url = f"https://api.opentripmap.com/0.1/en/places/radius?radius=5000&lon={city_lng}&lat={city_lat}&apikey=5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced"
        response = requests.get(opentripmap_url)
        data = response.json()

        # Check the data
        if 'features' in data and len(data['features']) > 0:
            for feature in data['features']:
                place_id = feature['properties']['xid']

                # Obtaining information about the places
                place_info_url = f"https://api.opentripmap.com/0.1/en/places/xid/{place_id}?apikey=5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced"
                response = requests.get(place_info_url)
                place_info = response.json()

                place_name = place_info['name']
                kinds = place_info.get('kinds', "").split(',')
                description = place_info.get('wikipedia_extracts', {}).get('text')
                rate = place_info.get('rate',0)
                image = place_info.get('preview',{}).get('source','')
                place_longitude = place_info.get('point', {}).get('lon', '')
                place_latitude = place_info.get('point', {}).get('lat', '')
                # print(f"kinds:{kinds}")

                # Creating node for the place
                session.run("""
                     MERGE (place:Place {name: $place_name})
                     SET place.desciption = $description, place.rate = $rate, place.image = $image, place.place_longitude = $place_longitude, place.place_latitude = $place_latitude
                 """, place_name=place_name, description=description, rate=rate, image=image, place_longitude=place_longitude, place_latitude=place_latitude)

		# Debugging
                #print("Place:", place_name)
                #print("Categories:", kinds)
                #print("Counter:", counter)

                # Creating relationships between clusters
                for cluster in clusters:
                    if any(category in kinds for category in cluster['categories']):
                        session.run("""
                            MATCH (place:Place {name: $place_name})
                            MATCH (cluster:Cluster {name: $cluster_name})
                            MERGE (place)-[:BELONGS_TO]->(cluster)
                        """, place_name=place_name, cluster_name=cluster['name'])
                       
                        session.run("""
                            MATCH (city:City {name: $city_name})
                            MATCH (cluster:Cluster {name: $cluster_name})
                            MERGE (city)-[:HAS_CLUSTER]->(cluster)
                        """, city_name=city_name, cluster_name=cluster['name']) 
                               
        else:
            print(f"No se encontraron lugares de interés para la ciudad {city_name}.")

    
    # Creating relationships between cities based on distances
    result = session.run("MATCH (city:City) RETURN city")
    for record in result:
        other_city = record["city"]
        if other_city["name"] != city_name:
           distance = calculate_distance(city_lat, city_lng, other_city["latitude"], other_city["longitude"])
           session.run("""
                MATCH (city1:City {name: $city1_name})
                MATCH (city2:City {name: $city2_name})
                MERGE (city1)-[:DISTANCE {value: $distance}]->(city2)
           """, city1_name=city_name, city2_name=other_city["name"], distance=distance)


# Closing Neo4j
driver.close()
