import web
from bus_core import haversine, build_stop_lookup, get_nearby_vehicles, get_fresh_feed, search_stops_by_name
import requests
from google.transit import gtfs_realtime_pb2
import os
import secrets
import requests

stops_lookup = build_stop_lookup() #Call def to cache and save stops.txt in a dictionary

urls = ( #create the urls for the website to access, this is web.py
    '/', 'index',
    '/stop/(.+)', 'stop_view',
    '/results', 'results',
    '/find_stop', 'find_stop',
    '/login',     'login',
    '/callback',  'callback'
)

app = web.application(urls, globals()) #call all the routes for web.py to use when running the app
render = web.template.render('templates/') # this is to be able to start using templates

#use web.py web session tool to create a session manager to start storing data in the browser during the login stage.
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'logged_in': False, 'user_email': None})

class index: #first class for the main initial page, the form with
    def GET(self):
        web.header('Content-Type', 'text/html; charset=utf-8')
        return render.index()

class stop_view: # this class is currently not being utilized and is part of previous test, feel free to ignore it
    def GET(self, stop_id):

        feed = get_fresh_feed()
        results = get_nearby_vehicles(stop_id, 5, stops_lookup, feed)

        if not results:
            return f"No vehicles found near stop {stop_id}"

        lines = [f"Vehicle {r['vehicle_id']}: {r['distance_km']:.2f} km" for r in results]
        return "<br>".join(lines)

class results: #this generates the results of stops after the user has entered the stop number and KMs desired for the radius
    def GET(self):
        user_data = web.input() #this basically helps us get the data that was input through the html forms and shown in the URL
        stop_id = user_data.stop_id #for example, in this case we get the stop ID

        try:

            radius_km = float(user_data.radius) #same here with the radius

        except ValueError:
            return "Please enter a valid number for radius." #Added try except to avoid entering letters or invalid values

        feed = get_fresh_feed() #this calls the get_fresh_feed function from bus_core.py
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

#With the login class we will be using Auth0, as for their SDK, it's unusable since it uses async and wait code, which is incompatible with web.py. We will manually issue requests to their endpoints for user registration and login with the help of requests and maybe Oauth2 python libraries in the future.
class login:
    def GET(self):
        domain = os.getenv('AUTH0_DOMAIN') #details are in the .env with the given credentials by Auth0, contact me if you need guidance with this.
        client_id = os.getenv('AUTH0_CLIENT_ID')
        state = secrets.token_urlsafe(16)

        auth_url = ( #request to authorize
            f"https://{domain}/authorize?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri=http://localhost:8080/callback&"
            f"scope=openid%20profile%20email&"
            f"state={state}"
        )

        return web.seeother(auth_url)

#callback for when the user has been successfully registered
class callback:
    def GET(self):
        user_data = web.input()
        code = user_data.code

        domain = os.getenv('AUTH0_DOMAIN')
        client_id = os.getenv('AUTH0_CLIENT_ID')
        client_secret = os.getenv('AUTH0_CLIENT_SECRET')

        token_response = requests.post( #request to receive token from Auth0 servers to be able to eventually access the user data
            f"https://{domain}/oauth/token",
            headers={"content-type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8080/callback",
            }
        )
        token_data = token_response.json() #make it json for convention
        access_token = token_data["access_token"] #save it in a dictionary

        userinfo_response = requests.get(
            f"https://{domain}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"} #request user info with the token we received for authentication
        )
        user_info = userinfo_response.json()

        return f"Logged in as: {user_info.get('email')}"

if __name__ == "__main__":
    app.run()
