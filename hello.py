import web
from bus_core import haversine, build_stop_lookup, get_nearby_vehicles, get_fresh_feed, search_stops_by_name
import requests
from google.transit import gtfs_realtime_pb2
import os

stops_lookup = build_stop_lookup() #Call def to cache and save stops.txt in a dictionary

urls = ( #create the urls for the website to access, this is web.py
    '/', 'index',
    '/stop/(.+)', 'stop_view',
    '/results', 'results',
    '/find_stop', 'find_stop'
)

app = web.application(urls, globals()) #call all the routes for web.py to use when running the app
render = web.template.render('templates/')

class index: #first class for the main initial page, the form with
    def GET(self):
        web.header('Content-Type', 'text/html; charset=utf-8')
        return render.index()

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

        try:

            radius_km = float(user_data.radius)

        except ValueError:
            return "Please enter a valid number for radius."

        feed = get_fresh_feed()
        vehicles = get_nearby_vehicles(stop_id, radius_km, stops_lookup, feed)

        if not vehicles:
            return f"No vehicles found near stop {stop_id}, also double check the stop entered exists!"


        return render.results(vehicles, stop_id)

class find_stop:
    def GET(self):
        user_data = web.input(stop_name=None)

        try:
            query = user_data.stop_name
        except ValueError:
            return "Please enter a valid stop name"

        if query is None or query.strip() == "":
            return render.find_stop(stops=None, query="")

        search_stop = search_stops_by_name(query, stops_lookup) 

        return render.find_stop(stops=search_stop, query=query)




if __name__ == "__main__":
    app.run()
