import requests
from geopy.geocoders import Nominatim

#Convert User Input Location to longitude, latitude
def convert_location(loc):
    geolocator = Nominatim(user_agent="Stargazing")
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
def moon_phase():
    return

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
        if weather_rating == "good":
            color = "\033[92m" #green
        else:
            color = "\033[91m" #red
        bold = "\033[1m"
        end = "\033[0m"
        moon_rating,phase = 'good',1
        overall_rating = 'good'
        print(f"{bold}Weather Rating: {end}{weather_rating.upper()} (Forecast: {forecast}, Temp: {night_temp} F)")
        print(f"{bold}Moon Rating: {end}{moon_rating.upper()} (Phase: {phase})")
        print(f"{bold}Overall Rating: {end}{overall_rating.upper()}")
        if (night_temp >=50) & (overall_rating == "good"): 
            print("Tonight's a great night to stargaze!")
        elif (night_temp <50) & (overall_rating == "good"):
            print("Tonight's a great night to stargaze! Make sure to bring a Jacket!")
        else:
            print("Maybe try again tomorrow!")
    except Exception as error:
        print(f"There was an error: {error}")
        
if __name__ == "__main__":
    main()