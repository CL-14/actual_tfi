from math import radians, sin, cos, sqrt, atan2
import csv
import requests
from google.transit import gtfs_realtime_pb2
import os
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

def build_stop_lookup():

        stop_dict = {}

        try:
            with open('GTFS_Realtime/stops.txt', newline='') as csvfile:
                stop_reading = csv.DictReader(csvfile)

                for row in stop_reading:
                    # Use stop_code as the main dictionary key, and store the entire row
                    stop_dict[row['stop_code']] = row


        except FileNotFoundError:
            print("The file 'stops.txt' was not found.")

        return stop_dict

def search_stops_by_name(query,stop_dict):

    stop_list = []

    query = query.strip().lower()

    for stop_data in stop_dict.values():

        stop_name = stop_data.get('stop_name', '')

        if query in stop_name.lower():
            stop_list.append(stop_data)

    return stop_list


def get_nearby_vehicles(stop_id, radius_km, stop_dict, feed): # Use CLI to pass stop id and km radius desired and return the number of vehicles within that radius of the stop.

    lat1 = 0
    lon1 = 0


    if stop_id not in stop_dict:
        print(f"Stop ID {stop_id} not found,")
        return []


    stop_row = stop_dict[stop_id] # this says, for the variable that will hold the rows of stops, get everything assigned to stop_id, which is the key, from the stop dictionary, remember this.

    lat1 = float(stop_row['stop_lat']) # this says, the lat1 will be taken from the existing row of stop info from stop_row, specifically stop_lat and be stored as a float in the variable. Remember this

    lon1 = float(stop_row['stop_lon'])

    ###### END OF FEED GET TROUBLESHOOT ######

    bus_info_list =[]


    for entity in feed.entity:
        if entity.HasField('vehicle'): # check if the entity has a vehicle field, if it does, then we can check its position and calculate the distance to the stop.
            lat2 = entity.vehicle.position.latitude #take the lat and lon of the vehicle from the API and pass it to the haversine formula to calculate distance.
            lon2 = entity.vehicle.position.longitude
            distance = haversine(lat1, lon1, lat2, lon2) #finally execute the function!

            if distance <= radius_km: #check if it's within the desired radius or nah
                bus_info_list.append({
                    "vehicle_id": entity.vehicle.vehicle.id,
                    "distance_km": distance,
                })


    return bus_info_list

#Get latest data from the NTA API
def get_fresh_feed():
    api_key = os.getenv('TFI_API_KEY')
    url = 'https://api.nationaltransport.ie/gtfsr/v2/vehicles'
    headers = {"x-api-key": api_key}

    feed = gtfs_realtime_pb2.FeedMessage()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        feed.ParseFromString(response.content)
        return feed
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return None
