import web
from bus_core import haversine, build_stop_lookup, get_nearby_vehicles, get_fresh_feed
import requests
from google.transit import gtfs_realtime_pb2
import os

stops_lookup = build_stop_lookup() #Call def to cache and save stops.txt in a dictionary

urls = ( #create the urls for the website to access, this is web.py
    '/', 'index',
    '/stop/(.+)', 'stop_view',
    '/results', 'results'
)

app = web.application(urls, globals()) #call all the routes for web.py to use when running the app

class index: #first class for the main initial page, the form with 
    def GET(self):
        web.header('Content-Type', 'text/html; charset=utf-8')
        return """
        <form action="/results" method="GET">
        <label for="stop_id">Stop Code:</label>
        <input type="text" id="stop_id" name="stop_id"><br><br>
        <label for="radius">Radius (km):</label>
        <input type="text" id="radius" name="radius"><br><br>
        <input type="submit" value="Search">
        </form>
        """

class stop_view:
    def GET(self, stop_id):

        feed = get_fresh_feed()
        results = get_nearby_vehicles(stop_id, 5, stops_lookup, feed)

        if not results:
            return f"No vehicles found near stop {stop_id}"

        lines = [f"Vehicle {r['vehicle_id']}: {r['distance_km']:.2f} km" for r in results]
        return "<br>".join(lines)

class results:
    def GET(self):
        user_data = web.input()
        stop_id = user_data.stop_id
        radius_km = float(user_data.radius)

        feed = get_fresh_feed()
        vehicles = get_nearby_vehicles(stop_id, radius_km, stops_lookup, feed)

        if not vehicles:
            return f"No vehicles found near stop {stop_id}, also double check the stop entered exists!"

        lines = [f"Vehicle {v['vehicle_id']}: {v['distance_km']:.2f} km" for v in vehicles]
        return "<br>".join(lines)

if __name__ == "__main__":
    app.run()
