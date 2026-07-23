import requests  # lets Python make web requests, like a browser fetching a page
from google.transit import gtfs_realtime_pb2  # gives the blueprint for reading GTFS-realtime's binary format
import os  # Python reads things from the OS, environment variables in this case
from math import radians, sin, cos, sqrt, atan2
import sys
import sqlite3
import time
import datetime
from bus_core import haversine, build_stop_lookup, get_nearby_vehicles

########### SETTING UP API KEY WITH ENV AND INITIALIZING THE SQLite DATABASE ###########

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

############# END OF BLOCK ############



stops_lookup = build_stop_lookup()

radius_km = float(sys.argv[1])

stop_ids = ["8269", "270", "277"] #stops to look for




feed = gtfs_realtime_pb2.FeedMessage()


while True: #infinite loop to keep checking the API every 60 seconds, until I stop it, to create some persistence.


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

     #check time so it can be added into the database, has to be refreshed every time the API is checked, so it has to be inside the while loop.

    time_checked = datetime.datetime.now()


    for stop_id in stop_ids:
        results = get_nearby_vehicles(stop_id, radius_km, stops_lookup, feed)

        for result in results:
            cur.execute("INSERT INTO bus_data (checked_at, stop_id, vehicle_id, distance_km) VALUES (?, ?, ?, ?)",
            (time_checked.strftime("%Y-%m-%d %H:%M:%S"), stop_id, result["vehicle_id"], result["distance_km"]))
            print(result)

    con.commit() #commit to the db

    time.sleep(60) #let it sleep zzz for 60 seconds befre the next request
