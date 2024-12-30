#check if all packages are installed
import sys
import subprocess
import os

#force default path to be the working directory
default_path = os.getcwd()
os.chdir(default_path)

#required packages
required_packages = ['warnings','requests','datetime','ephem','skyfield','pandas','math','matplotlib','geopy','rich','astropy','suntime']

#install packages if necessary
def packages_install(required_packages):
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Package {package} is not installed. Installing...")
            subprocess.check_call([sys.executable,"-m","pip","install",package])
        else:
            print(f"Package {package} is already installed.")
    return

packages_install(required_packages)

import warnings
import requests
import datetime
import ephem
import skyfield.almanac as almanac
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from suntime import Sun
from skyfield.data import hipparcos
from geopy.geocoders import Nominatim
from skyfield.api import load
from rich.progress import Progress
from astropy.coordinates import AltAz
from astropy.coordinates import EarthLocation, SkyCoord

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
            moon_phase_rating = "OK"
        if (90 <= phase_deg <=180):
            moon_phase = "Waxing Gibbous"
            moon_phase_rating = "Not Good"
        if (180 <= phase_deg <=270):
            moon_phase = "Waning Gibbous"
            moon_phase_rating = "Not Good"
        if (270 <= phase_deg <= 360):
            moon_phase = "Waning Crescent"
            moon_phase_rating = "OK"
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
    rating_text = "great" if rating >=9 else "pretty good" if 7<= rating <9 else "pretty bad" if 4<= rating <7 else "bad"
    return rating, rating_text

#get accurate sunrise and sunset
def sunrise_sunset(lat,long):
    sun = Sun(lat, long)
    sunrise = sun.get_local_sunrise_time()
    sunset = sun.get_local_sunset_time()
    #above doesn't fully work, need to manually get correct time
    local_sunrise = sunrise - datetime.timedelta(hours=6)
    local_sunset = sunset + datetime.timedelta(hours=18)
    return local_sunrise, local_sunset

#Find Cool Objects
#use the hipparcos dataset
def visible_stars(lat,long):
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
    #date_today = datetime.date.today()
    #date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    #night_time_start = Time(f'{date_today} 18:00:00')
    #night_time_end = Time(f'{date_tomorrow} 06:00:00')
    night_time_end,night_time_start = sunrise_sunset(lat,long)
    night_time_end += datetime.timedelta(hours=24)
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
        #of ~10 deg or something because there will be stuff in the way. 
        if (altitude_start > 15) | (altitude_end > 15):
            visibilities.append('visible')
        else:
            visibilities.append('not visible')
    stars_names["visible?"] = visibilities
    #get rid of the not visible ones
    final_star_catalog = stars_names[stars_names["visible?"]=='visible']
    bright_visible_objects = final_star_catalog.head(5)['name'].tolist() #only need a few  
    return bright_visible_objects

def visible_planets(lat,long):
    #set up observer stuff
    observer = ephem.Observer()
    observer.lat=str(lat)
    observer.lon=str(long)
    #get date
    #date_today = datetime.datetime.now()
    #observer.date = date_today
    #night_time_start = date_today.replace(hour=18,minute=0,second=0,microsecond=0)
    #night_time_end = night_time_start + datetime.timedelta(hours=12)
    night_time_end,night_time_start = sunrise_sunset(lat,long)
    night_time_end += datetime.timedelta(hours=24)
    #planet altitudes
    planets = [ephem.Mercury(),ephem.Venus(),ephem.Mars(),ephem.Jupiter(),ephem.Saturn(),ephem.Uranus(),ephem.Neptune()]
    visible_planets = []
    current_time = night_time_start
    #loop over time range, check every hour
    while current_time < night_time_end:
        observer.date = current_time
        for planet in planets:
            planet.compute(observer)
            alt_deg = planet.alt * (180/ephem.pi) #convert to deg
            #I use a sort of arbitrary cutoff of 5 deg altitude because something at say
            #5 deg is going to be very hard to see
            if (alt_deg>15) & (planet.name not in visible_planets):
                visible_planets.append(planet.name)
        current_time += datetime.timedelta(hours=1)
    return visible_planets

def haversine_distance(lat1,long1,lat2,long2):
#finds distance between two lat,long coordinates
#adapted from stackoverflow post https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    #convert demical to radians
    lat1, long1, lat2, long2 = map(math.radians,[lat1,long1,lat2,long2])
    delta_lat = lat2 - lat1
    delta_long = long2 - long1
    #apply the formula
    r = 3963 #miles = radius of earth
    dist = 2 * r * (math.asin(((math.sin(delta_lat/2)**2) + math.cos(lat1) * math.cos(lat2) * (math.sin(delta_long/2)**2))**(1/2)))
    return dist

def shortest_distance(lat,long,points):
#finds the shortest distance using the haversine distance
    distances = []
    for point in points:
        distances.append((haversine_distance(lat,long,point['lat'],point['long']),point))
    shortest_dist, closest_point = min(distances,key = lambda x: x[0])
    return shortest_dist, closest_point["Name"], closest_point["lat"],closest_point["long"]

def light_pollution(lat,long,location,lat2,long2,location2,dist,zoom=12):
    #night sky map with some markers
    warnings.simplefilter(action='ignore')
    image_path = "BlackMarble_2016_3km.jpg"
    light_map = mpimg.imread(image_path)

    map_extent = [-180,180,-90,90] #[min_lon,max_lon,min_lat,max_lat]
    #gneral map settings
    plt.figure(figsize=(12,8))
    plt.imshow(light_map, extent=map_extent, aspect='auto')
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    #plt.xlim([-135,-55])  #Contintental US only
    #plt.ylim([25,60])
    plt.xlim([long-zoom,long+zoom]) #zooms in to give a better look
    plt.ylim([lat-zoom,lat+zoom])
    plt.axis('off')
    plt.subplots_adjust(left=0,right=1,top=1,bottom=0)
    #plot markets on map
    plt.plot(long, lat, 'ro', markersize=8) 
    plt.text(long - 2.5, lat + 0.5, location, fontsize=14, color='red',weight='bold', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))
    plt.plot(long2, lat2, 'go', markersize=8)
    #handles overlapping text decently well
    long2_offset = 1 if long2 > long else -1
    lat2_offset = 1 if lat2 > lat else -1
    plt.text(long2 + long2_offset, lat2 + lat2_offset, location2, fontsize=14, color='green',weight='bold', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))
    plt.text(long - 3.5,lat + 7, "Nearest Dark Site",color='white',weight='bold',fontsize=32)
    plt.text(long - 0.75,lat + 6, f"{dist:.0f} mi away", color='white',weight ='bold',fontsize=17)
    plt.show(block=True)
    return

#user input
welcome_message = """
Welcome to StargazingV1! Let's see if you can stargaze tonight!
(MAKE SURE TO CHECK TERMINAL OUTPUT FOR ALL INFO AFTER RUNNING)
Input a Location:
"""
#Execute
def main():
    while True:
        location = input(welcome_message)
        try:
            #progres bar
            with Progress(transient=True) as progress:

                #separate stuff into tasks
                progress_bar = progress.add_task("[white]Calculating...", total=14)

                #call the functions
                latitude, longitude = convert_location(location)
                progress.update(progress_bar,advance=2)

                forecast, weather_rating, night_temp = get_weather(latitude,longitude)
                progress.update(progress_bar,advance=2)

                moon_phase, moon_phase_rating, illumination = get_moon_phase()
                progress.update(progress_bar,advance=2)

                visible_star_list = visible_stars(latitude,longitude)
                visible_planet_list = visible_planets(latitude,longitude)
                progress.update(progress_bar,advance=2)

                overall_rating_number, overall_rating_text = calculate_rating(illumination,night_temp,weather_rating)
                progress.update(progress_bar,advance=2)

                #dark sky
                dark_sky_sites = pd.read_csv('dark_sites_us.csv', usecols=['Name','lat','long'])
                dark_sky_sites_dict = dark_sky_sites.to_dict(orient='records')
                shortest_dist, closest_site, dark_site_lat,dark_site_long = shortest_distance(latitude,longitude,dark_sky_sites_dict)
                progress.update(progress_bar,advance=2)

                #pretty text styling
                bold = "\033[1m"   
                end = "\033[0m"
                underline = "\033[4m"
                green = "\033[92m"
                red = "\033[91m"

                if weather_rating == "good":
                    weather_color = green 
                else:
                    weather_color = red
                if moon_phase_rating == "Great":
                    moon_color = green
                elif moon_phase_rating == "OK":
                    moon_color = green
                else:
                    moon_color = red
                if overall_rating_text == ("great") or overall_rating_text == ("pretty good"):
                    overall_color = green
                elif overall_rating_text == ("bad") or overall_rating_text == ("pretty bad"):
                    overall_color = red

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
                        print(f"{underline}Tonight's a GREAT night to stargaze! Make sure to bring a Jacket!{end}")
                    elif overall_rating_text == "pretty good":
                        print(f"{underline}It might not be perfect but go for it! Make sure to bring a Jacket!{end}")
                    elif overall_rating_text == "pretty bad":
                        print(f"{underline}Not a good night, but who's stopping you! Make sure to bring a Jacket if you go!{end}")
                    else:
                        print(f"{underline}Try again another night.{end}")
                print("----------------------------------------------------------------")
                print("Some Extra Info:")
                print("")
                print(f"The closest official {underline}dark site{end} to you:")
                #f strings behave weird for older versions of python, had to do this print statement differently
                print('\033[96m' + str(closest_site) + ' (' + str(round(shortest_dist,2)) +' mi away) \033[0m')
                print("")
                print(f"Here are some cool visible {underline}stars{end} tonight:")
                print("\033[95m"+ ", ".join(map(str,visible_star_list))+"\033[0m")
                if len(visible_planet_list) > 0:
                    print(f"Here are the visible {underline}planets{end} tonight:")
                print("\033[95m"+ ", ".join(map(str,visible_planet_list))+"\033[0m")
                print("----------------------------------------------------------------")
                print("")
                progress.update(progress_bar,advance=2)
                light_pollution(latitude,longitude,location,dark_site_lat,dark_site_long,closest_site,shortest_dist) #show light map

        except Exception as error:
            print(f"There was an error: {error}")
        
        #allow for continued input
        print("")
        retry = input('Would you like to look at another location? (y/n):').strip().lower()
        if retry not in ['y']:
            print('Thank you for using StargazingV1!')
            break
if __name__ == "__main__":
    main()