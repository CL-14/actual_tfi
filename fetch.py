import requests  # lets Python make web requests, like a browser fetching a page
from google.transit import gtfs_realtime_pb2  # gives the blueprint for reading GTFS-realtime's binary format
import os  # Python reads things from the OS, environment variables in this case
from math import radians, sin, cos, sqrt, atan2
import csv
import sys
import sqlite3
import datetime
import time
api_key = os.getenv('TFI_API_KEY')  # reads the API key stored as an env variable, so it's not hardcoded in the file, don't mess up

con = sqlite3.connect("TFI.db") #this creates the db if it doesn't exist already and connects to it!

cur = con.cursor() # a "cursor" is what lets allows to execute SQL commands in the database, that's why we need to create one here.

# Create the table if it doesn't exist already, with the specified columns and data types.
cur.execute (""" CREATE TABLE IF NOT EXISTS bus_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at TEXT,
    stop_id TEXT,
    vehicle_id TEXT,
    distance_km REAL
)""")
con.commit()

url = 'https://api.nationaltransport.ie/gtfsr/v2/vehicles'  # the address you're asking for data
headers = {"x-api-key": api_key}  # extra info sent with the request

def haversine(lat1, lon1, lat2, lon2):  # calculate the haversine distance between two points on earth.

            lat1 = radians(lat1)
            lon1 = radians(lon1)
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


while True: #infinite loop to keep checking the API every 60 seconds, until I stop it, to create some persistence.


    feed = gtfs_realtime_pb2.FeedMessage()

    try: # make the request to the API and handle potential errors
        response = requests.get(url, headers=headers, timeout=10)

        # Raises an HTTPError if the response was an HTTP error code (e.g., 401, 403, 429 Rate Limited, 500)
        response.raise_for_status()

        print(f"HTTP Status Code: {response.status_code} (Success)")

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
        if response.status_code == 429:
            print("Rate limit exceeded! You are making requests too quickly.")
            sys.exit(1)
        elif response.status_code == 401 or response.status_code == 403:
            print("Authentication error. Check your API key or headers.")
        sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("Connection Error: Failed to connect to the server. Check your internet connection.")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print("Timeout Error: The server took too long to respond.")
        sys.exit(1)

    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred during the request: {err}")
        sys.exit(1)

    # Parse the raw bytes into the GTFS container safely
    try:
        feed.ParseFromString(response.content)
    except Exception as e:
        print(f"Failed to parse GTFS-realtime feed data: {e}")
        sys.exit(1)

    time_checked = datetime.datetime.now() #check time so it can be added into the database, has to be refreshed every time the API is checked, so it has to be inside the while loop.



    def get_nearby_vehicles(stop_id, radius_km): # Use CLI to pass stop id and km radius desired and return the number of vehicles within that radius of the stop.
        lat1 = 0
        lon1 = 0
        stop_found = False

        try:
            with open('GTFS_Realtime/stops.txt', newline='') as csvfile:  #read docs of csv.DictReader, then pass the values found to the variables for the formula.
                Stop_iteration = csv.DictReader(csvfile)

                for row in Stop_iteration:
                    if row['stop_code'] == stop_id:
                        lat1 = float(row['stop_lat']) #csv returns strings, so we have to convert them to floats for the haversine formula to work.
                        lon1 = float(row['stop_lon'])
                        print(row['stop_code'], row['stop_name'], lat1, lon1) #make sure to print this to know if the stop id is being found correctly.
                        stop_found = True
                        break
        except FileNotFoundError:
            print("The file 'stops.txt' was not found. Please ensure it exists in the 'GTFS_Realtime' directory.")#make sure the stops exist xd
            return

        if not stop_found:
            print(f"Stop ID {stop_id} not found in stops.txt.") #prevent entering non-existen stop ids
            return

        for entity in feed.entity:
                if entity.HasField('vehicle'):
                    lat2 = entity.vehicle.position.latitude #take the lat and lon of the vehicle from the API and pass it to the haversine formula to calculate distance.
                    lon2 = entity.vehicle.position.longitude
                    near_entities = haversine(lat1, lon1, lat2, lon2) #finally execute the function!

                    if near_entities <= radius_km: #check if it's within the desired radius or nah
                        print(f"Vehicle ID: {entity.vehicle.vehicle.id}, Distance: {near_entities:.2f} km. It is within {radius_km} kms or less of stop {stop_id}!")

                        cur.execute("INSERT INTO bus_data (checked_at, stop_id, vehicle_id, distance_km) VALUES (?, ?, ?, ?)",
                                    (time_checked.strftime("%Y-%m-%d %H:%M:%S"), stop_id, entity.vehicle.vehicle.id, near_entities)) #after every check has passed, insert it to the database with all the info needed!

        con.commit() #commit to the db


    result = get_nearby_vehicles(sys.argv[1], float(sys.argv[2])) # pass the stop id and radius in km as command line arguments when running the script, e.g., python fetch.py 12345 1.5

    print(time_checked.strftime("%c")) #testing datetime alone

    time.sleep(60) #let it sleep zzz for 60 seconds befre the next request
