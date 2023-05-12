import requests
import pandas as pd

city_names=[]
lats=[]
longs=[]

url = "http://api.geonames.org/searchJSON?q=&country=ES&adminCode1=&maxRows=1000&username=pslasso&featureClass=P"
response = requests.get(url)
data = response.json()
if "geonames" in data:
    cities = [place["toponymName"] for place in data["geonames"]]
    print(cities)

cities    
    
for city in cities:
    resp = requests.get("https://api.opentripmap.com/0.1/en/places/geoname?name="+city+"&country=es&apikey=5ae2e3f221c38a28845f05b6611d689a2de8f6f04047db87740dc9ca").json()
    city_names.append(resp['name'])
    lats.append(resp['lat'])
    longs.append(resp['lon'])


print(city_names, lats, longs)

tuples = list(zip(city_names, lats, longs))

tuples

citi_data=pd.DataFrame(tuples, columns=["City", "Lat", "Lon"]) 


print(citi_data.head()) 

citi_data.to_csv("/home/paul/Documents/DataScientestProject/cities.csv") #exportar csv



