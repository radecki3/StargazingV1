import warnings
import requests
import datetime
import ephem
import skyfield.almanac as almanac
import pandas as pd
from skyfield.data import hipparcos
from geopy.geocoders import Nominatim
from skyfield.api import load
from rich.progress import Progress
from astropy.coordinates import AltAz
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time

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
    #there's a depreciation warning that is annoying
    warnings.simplefilter(action='ignore',category=FutureWarning)
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

#Calculate a score for the night out of 10 based on various factors, this is kind of arbitrary
def calculate_rating(illum, temp, weather_rating):
    dummy_rating = 0
    dummy_rating += 0.5 if temp >=50 else 0.5 if temp >=40 else 0
    dummy_rating += 6 if weather_rating == "good" else 0
    if illum <= 2:
        dummy_rating +=3
    elif 2 < illum <= 10:
        dummy_rating +=2.5
    elif 10 < illum <= 30:
        dummy_rating +=2
    elif 30 < illum <= 50:
        dummy_rating +=1.5
    elif 50 < illum <= 70:
        dummy_rating +=1.0
    rating = dummy_rating
    rating_text = "great" if rating >=9 else "pretty good" if 7< rating <10 else "pretty bad" if 4< rating <7 else "bad"
    return rating, rating_text

#Find Cool Objects
#use the hipparcos dataset
def visible_objects(lat,long):
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)
    brightest_stars = df[df.magnitude < 1.0].sort_values('magnitude').reset_index() #magniutdes are in reverse order of brightness
    brightest_stars = brightest_stars[['hip','magnitude','ra_degrees','dec_degrees']]
    #get common names of brightest stars, this is from a separate catalog
    #https://www.celestialprogramming.com/snippets/StarCommonNamesWithHipRADecMag.json
    name_references = pd.read_json('StarCommonNamesWithHipRADecMag.json')
    common_names = pd.DataFrame({"name": name_references[0][1:],"hip": name_references[1][1:]})
    #assigns names to brightest stars
    stars_names = pd.merge(brightest_stars,common_names,on="hip",how="inner")
    #get altitude and azimuth
    date_today = datetime.date.today()
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    night_time_start = Time(f'{date_today} 18:00:00')
    night_time_end = Time(f'{date_tomorrow} 06:00:00')
    location = EarthLocation(lat=lat,lon=long)
    altaz_converter_start = AltAz(location=location,obstime=night_time_start)
    altaz_converter_end = AltAz(location=location,obstime=night_time_end)
    #loop over dataframe and convert stars positions to alt az
    star_alt_start = []
    star_alt_end = []
    for idx, star in stars_names.iterrows():
        star_ra = star['ra_degrees']
        star_dec = star['dec_degrees']
        star_coord = SkyCoord(f'{star_ra}',f'{star_dec}',unit='deg')
        star_coord_start = star_coord.transform_to(altaz_converter_start)
        star_coord_end = star_coord.transform_to(altaz_converter_end)
        star_alt_start.append(star_coord_start.alt.degree)
        star_alt_end.append(star_coord_end.alt.degree)
    stars_names["altitude_start"] = star_alt_start
    stars_names["altitude_end"] = star_alt_end
    #check if stars are visible
    visibilities = []
    for row in stars_names.iterrows():
        altitude_start = row[1][5]
        altitude_end = row[1][6]
        #technically, altitude >0 means it will be above the horizon but really it's hard to see anything below an altitude
        #of ~5 deg or something because there will be stuff in the way. 
        if (altitude_start > 5) | (altitude_end > 5):
            visibilities.append('visible')
        else:
            visibilities.append('not visible')
    stars_names["visible?"] = visibilities
    #get rid of the not visible ones
    final_star_catalog = stars_names[stars_names["visible?"]=='visible']
    bright_visible_objects = final_star_catalog.head(5)['name'].tolist() #only need a few  
    return bright_visible_objects

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
        #progres bar
        with Progress(transient=True) as progress:

            #separate stuff into tasks
            progress_bar = progress.add_task("[White]Calculating...", total=10)

            #call the functions
            latitude, longitude = convert_location(location)
            progress.update(progress_bar,advance=2)

            forecast, weather_rating, night_temp = get_weather(latitude,longitude)
            progress.update(progress_bar,advance=2)

            moon_phase, moon_phase_rating, illumination = get_moon_phase()
            progress.update(progress_bar,advance=2)

            visible_star_list = visible_objects(latitude,longitude)
            progress.update(progress_bar,advance=2)

            overall_rating_number, overall_rating_text = calculate_rating(illumination,night_temp,weather_rating)
            progress.update(progress_bar,advance=2)

            #pretty text styling
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
            if overall_rating_text == ("great") or overall_rating_text == ("pretty good"):
                overall_color = "\033[92m"
            elif overall_rating_text == ("bad") or overall_rating_text == ("pretty bad"):
                overall_color = "\033[91m"
            bold = "\033[1m"   
            end = "\033[0m"

            #a bunch of print statements
            print("")
            print("----------------------------------------------------------------")
            print(f"Stagazing Quality for \033[94m{location}{end} tonight:")
            print(f"{bold}Weather Rating: {end} {weather_color}{weather_rating.upper()}{end} (Forecast: {forecast}, Temp: {night_temp} F)")
            print(f"{bold}Moon Rating: {end} {moon_color}{moon_phase_rating.upper()}{end} (Phase: {moon_phase}, {illumination:.2f}% Illuminated)")
            print(f"{bold}Overall Rating: {end}{overall_color}{overall_rating_text.upper()}{end} (Rating: {overall_rating_number}/10)")
            print("")

            if night_temp >=50:
                if overall_rating_text == "great": 
                    print("Tonight's a GREAT night to stargaze!")
                elif overall_rating_text == "pretty good":
                    print("It might not be perfect but go for it!")
                elif overall_rating_text == "pretty bad":
                    print("Not a good night, but who's stopping you!")
                else:
                    print("Try again another night.")
            else:
                if (overall_rating_text == "great"):
                    print("Tonight's a GREAT night to stargaze! Make sure to bring a Jacket!")
                elif overall_rating_text == "pretty good":
                    print("It might not be perfect but go for it! Make sure to bring a Jacket!")
                elif overall_rating_text == "pretty bad":
                    print("Not a good night, but who's stopping you! Make sure to bring a Jacket if you go!")
                else:
                    print("Try again another night.")
            print("")
            print("Here are some cool visible stars tonight:")
            print("\033[95m"+ ", ".join(map(str,visible_star_list))+"\033[0m")
            print("----------------------------------------------------------------")
            print("")
            
    except Exception as error:
        print(f"There was an error: {error}")
        
if __name__ == "__main__":
    main()