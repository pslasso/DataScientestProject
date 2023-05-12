import pandas as pd
import requests

df = pd.read_csv("/home/paul/Documents/Project/cities_data.csv")

cities = []
lons = []
lats = []
names = []
kinds = []

for i in range(36):
    lon = str(df['Lon'].iloc[i])
    lat = str(df['Lat'].iloc[i])
    response = requests.get("https://api.opentripmap.com/0.1/en/places/radius?radius=1000&lon="+lon+"&lat="+lat+"&apikey=5ae2e3f221c38a28845f05b60b17b7c3473712177ccd23d0247a7ced")
    data = response.json()
    for place in data['features']:
        cities.append(df['City'].iloc[i])
        lons.append(place['geometry']['coordinates'][0])
        lats.append(place['geometry']['coordinates'][1])
        names.append(place['properties']['name'])
        kinds.append(place['properties']['kinds'])
        
        


tuples = list(zip(cities, names, lons, lats, kinds))

tuples

places = pd.DataFrame(tuples, columns=["city", "Name", "Lon", "Lat", "Kind"]) 

print(places)

places.to_csv("/home/paul/Documents/Project/places.csv")