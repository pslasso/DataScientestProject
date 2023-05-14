import pandas as pd
import requests
import csv

df = pd.read_csv("/home/paul/Documents/Project/cities_data.csv")

cities = []
lons = []
lats = []
names = []
kinds = []



for i in range(1000):  
    lon = str(df['Lon'].iloc[i])
    lat = str(df['Lat'].iloc[i])
    response = requests.get("https://api.opentripmap.com/0.1/en/places/radius?radius=1000&lon="+lon+"&lat="+lat+"&rate=3&apikey=5ae2e3f221c38a28845f05b6611d689a2de8f6f04047db87740dc9ca")
    if response.status_code == 200:
        data = response.json()
        print(response)
        for place in data['features']:
            cities.append(df['City'].iloc[i])
            lons.append(place['geometry']['coordinates'][0])
            lats.append(place['geometry']['coordinates'][1])
            names.append(place['properties']['name'])
            kinds.append(place['properties']['kinds'])
        


tuples = list(zip(cities, names, lons, lats, kinds))

tuples

places = pd.DataFrame(tuples, columns=["City", "Name", "Lon", "Lat", "Kind"]) 

print(places)

places.to_csv("/home/paul/Documents/DataScientestProject/places.csv")



#with open('places.csv','a') as fd:
#    writer = csv.writer(fd)
#    for row in places:
#        writer.writerow(row)