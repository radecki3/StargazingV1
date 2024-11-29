import requests
import datetime
import ephem
import skyfield.almanac as almanac
from geopy.geocoders import Nominatim
from skyfield.api import load

#Convert User Input Location to longitude, latitude
def convert_location(loc):
    geolocator = Nominatim(user_agent='Stargazing')
    #location
    location = geolocator.geocode(loc)
    lat = location.latitude
    long = location.longitude
    if location:
        return lat,long
    else:
        return f"Location {loc} not found. Try rewording address."

#Get Weather Data from NWS
def get_weather(lat,long):
    #have to first fetch grid points
    grid_url = f"https://api.weather.gov/points/{lat},{long}"
    #NWS does not use API keys
    headers = {"User-Agent": "(stargazing_script,stargazing_email)"}
    r_grid = requests.get(grid_url,headers=headers)
    status_code_grid = r_grid.status_code
    #status code 400 or 500 means an invalid request
    if status_code_grid >= 400:
        return "Invalid Grid Request"
    #data is in json format, get grid points
    grid_properties = r_grid.json()["properties"]
    gridId = grid_properties["gridId"]
    gridX = grid_properties["gridX"]
    gridY = grid_properties["gridY"]
    #now get actual forecast
    forecast_url = f"https://api.weather.gov/gridpoints/{gridId}/{gridX},{gridY}/forecast"
    r_forecast = requests.get(forecast_url,headers=headers)
    status_code_forecast = r_forecast.status_code
    if status_code_forecast >= 400:
        return "Invalid Forecast Request"
    #get desired forecast, for "tonight", which is a 12 hour period
    forecast_properties = r_forecast.json()["properties"]["periods"][0]
    #different places have different weather descriptors. this should cover most of them.
    bad_weather = ["cloud","rain","fog","snow","shower","thunderstorm","sleet","drizzle","haze","overcast","flurries"]
    #if you make this request at different times the first period forecast could be daytime, which is not useful here.
    if forecast_properties["isDaytime"] == False:
        night_temp = forecast_properties["temperature"] #let's store this for fun
        short_forecast = (forecast_properties["shortForecast"]).lower()
        if any(weather in short_forecast for weather in bad_weather):
            weather_rating = "bad"
        else:
            weather_rating = "good"
    else:
        forecast_properties = r_forecast.json()["properties"]["periods"][1]
        night_temp = forecast_properties["temperature"]
        short_forecast = (forecast_properties["shortForecast"]).lower()
        if any(weather in short_forecast for weather in bad_weather):
            weather_rating = "bad"
        else:
            weather_rating = "good"
    return short_forecast, weather_rating, night_temp

#Get Moon Phase
def get_moon_phase():
    #today's date
    current_date = datetime.date.today()
    #moon illumination, with some error tolerance
    illumination = ephem.Moon(current_date).phase
    if illumination >=98:
        moon_phase = "Full Moon"
        moon_phase_rating = "Bad"
    elif illumination <=2:
        moon_phase = "New Moon"
        moon_phase_rating = "Great"
    else: #need this other package to distinguish phases
        eph = load('de421.bsp') #JPL moon phase catalog
        moon = eph['moon']
        ts = load.timescale()
        current_time = ts.utc(current_date)
        phase_deg = (almanac.moon_phase(eph,current_time)).degrees #returns in deg
        if (0 <= phase_deg <= 90):
            moon_phase = "Waxing Crescent"
            moon_phase_rating = "Pretty Good"
        if (90 <= phase_deg <=180):
            moon_phase = "Waxing Gibbous"
            moon_phase_rating = "Not Good"
        if (180 <= phase_deg <=270):
            moon_phase = "Waning Gibbous"
            moon_phase_rating = "Not Good"
        if (270 <= phase_deg <= 360):
            moon_phase = "Waning Crescent"
            moon_phase_rating = "Pretty Good"
    #for me, if it's a new moon that's great, crescent is stil okay, gibbous is pretty bad, full moon is very bad
    return moon_phase, moon_phase_rating, illumination

#Combine
def calculate_rating():
    return

#user input
welcome_message = """
Welcome to StargazingV1! 
Let's see if you can stargaze tonight!
Input a Location:
"""
#Execute
def main():
    location = input(welcome_message)
    try:
        latitude, longitude = convert_location(location)
        forecast, weather_rating, night_temp = get_weather(latitude,longitude)
        moon_phase, moon_phase_rating, illumination = get_moon_phase()
        if weather_rating == "good":
            weather_color = "\033[92m" #green
        else:
            weather_color = "\033[91m" #red
        if moon_phase_rating == "Great":
            moon_color = "\033[92m" 
        elif moon_phase_rating == "Pretty Good":
            moon_color = "\033[92m" 
        else:
            moon_color = "\033[91m"
        bold = "\033[1m"
        end = "\033[0m"
        overall_rating = 'good'
        print(f"{bold}Weather Rating: {end} {weather_color}{weather_rating.upper()}{end} (Forecast: {forecast}, Temp: {night_temp} F)")
        print(f"{bold}Moon Rating: {end} {moon_color}{moon_phase_rating.upper()}{end} (Phase: {moon_phase}, {illumination:.2f}% Illuminated)")
        print(f"{bold}Overall Rating: {end}{overall_rating.upper()}")
        if (night_temp >=50) & (overall_rating == "good"): 
            print("Tonight's a great night to stargaze!")
        elif (night_temp <50) & (overall_rating == "good"):
            print("Tonight's a great night to stargaze! Make sure to bring a Jacket!")
        else:
            print("Try again tomorrow!")
    except Exception as error:
        print(f"There was an error: {error}")
        
if __name__ == "__main__":
    main()