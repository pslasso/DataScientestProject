from fastapi import FastAPI
from py2neo import Graph
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS headers to allow requests from the client origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to the Neo4j database
graph = Graph("bolt://my-neo4j-container:7687", auth=("neo4j", "aleneo4j"))


@app.get("/cities")
def get_cities() -> List[str]:
    query = """
    MATCH (c:City)
    RETURN c.name AS city
    ORDER BY c.name
    """
    result = graph.run(query)
    cities = [record["city"] for record in result.data()]
    return cities


@app.get("/places/{city}")
def get_places(city: str) -> List[str]:
    query = """
    MATCH (city:City {name: $city})-[:HAS_CLUSTER]->(:Cluster)<-[:BELONGS_TO]-(place:Place)
    RETURN place.name AS placeName
    """
    result = graph.run(query, city=city)
    places = [record["placeName"] for record in result.data()]
    return places


@app.get("/itinerary/{cities}/{cluster}")
def generate_itinerary(cities: str, cluster: str) -> List[dict]:
    cities_list = cities.split(",")

    query = """
    MATCH (city:City)-[:HAS_CLUSTER]->(:Cluster {name: $cluster})<-[:BELONGS_TO]-(place:Place)
    WHERE city.name IN $cities
    RETURN place.name AS placeName, city.name AS cityName, place.description AS description,
           place.rate AS rate, place.image AS image, place.place_longitude AS placeLongitude,
           place.place_latitude AS placeLatitude
    """
    result = graph.run(query, cluster=cluster, cities=cities_list)
    itinerary = [
        {
            "placeName": record["placeName"],
            "cityName": record["cityName"],
            "description": record["description"],
            "rate": record["rate"],
            "image": record["image"],
            "placeLongitude": record["placeLongitude"],
            "placeLatitude": record["placeLatitude"]
        }
        for record in result.data()
    ]
    return itinerary

@app.get("/city/{name}")
def get_city_coordinates(name: str) -> dict:
    query = """
    MATCH (c:City)
    WHERE c.name = $name
    RETURN c.latitude AS latitude, c.longitude AS longitude
    """
    result = graph.run(query, name=name)
    record = result.data()[0]
    city_data = {"latitude": record["latitude"], "longitude": record["longitude"]}
    return city_data


@app.get("/route/{city1}/{city2}")
def calculate_distance(city1: str, city2: str) -> float:
    query = """
    MATCH (c1:City {name: $city1})<-[distance:DISTANCE]-(c2:City {name: $city2})
    RETURN distance.value AS distance
    """
    result = graph.run(query, city1=city1, city2=city2)
    records = result.data()
    if records:
        distance = records[0]["distance"]
        return distance
    else:
        return None


@app.post("/cities")
def add_city(city: str):
    query = """
    CREATE (:City {name: $city})
    """
    result = graph.run(query, city=city)
    if result:
        return {"message": "City added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add city")


@app.delete("/cities/{city}")
def delete_city(city: str):
    query = """
    MATCH (c:City {name: $city})
    DETACH DELETE c
    """
    result = graph.run(query, city=city)
    if result:
        return {"message": "City deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete city")

