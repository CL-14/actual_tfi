import requests  # lets Python make web requests, like a browser fetching a page
from google.transit import gtfs_realtime_pb2  # gives the blueprint for reading GTFS-realtime's binary format
import os  # Python reads things from your operating system, environment variables in this case
from math import radians, sin, cos, sqrt, atan2

api_key = os.getenv('TFI_API_KEY')  # reads the API key stored as an env variable, so it's not hardcoded in the file, don't mess up

url = 'https://api.nationaltransport.ie/gtfsr/v2/vehicles'  # the address you're asking for data
headers = {"x-api-key": api_key}  # extra info sent with the request

feed = gtfs_realtime_pb2.FeedMessage()  # an empty container shaped exactly like GTFS-realtime data
response = requests.get(url, headers=headers)  # actually go fetch the data from the server
feed.ParseFromString(response.content)  # take the raw bytes you got back and pour them into the container, now it's structured data

lat1 = radians(53.403188)
lon1 = radians(-6.259829)

def haversine(lat1, lon1, lat2, lon2):

            # lat1 = radians(lat1) #not needed since lat1 and lon1 are already converted to radians
            # lon1 = radians(lon1)
            lat2 = radians(lat2)
            lon2 = radians(lon2)

            #calculate the difference, that is, subtracting the two latitudes and longitudes from each other
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            #calculate the haversine formula
            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

            #calculate the great circle distance in radians
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            r = 6371.0  # Radius of earth in kilometers.

            distance = r * c

            return distance

count = 0

for entity in feed.entity:  # feed.entity is a list of "things reported" — each one might be a vehicle, a trip update, or an alert
    if entity.HasField('vehicle'):  # check: is this specific entity actually a vehicle report?


        lat2 = entity.vehicle.position.latitude
        lon2 = entity.vehicle.position.longitude

        distance_km = haversine(lat1, lon1, lat2, lon2)

        if distance_km <= 5:
            count += 1
            print (f"Vehicle ID: {entity.vehicle.vehicle.id}, Distance: {distance_km:.2f} km. It is within 5 km or less of the specified location!!")

print(f"Total number of vehicles within 5 km: {count}")
