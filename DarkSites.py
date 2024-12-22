import pandas as pd
from geopy.geocoders import Nominatim
import time

#get "official" list of dark sites from wiki

url = 'https://en.wikipedia.org/wiki/Dark-sky_preserve'

dark_sky_table = pd.read_html(url)[0]
dark_sky_table_us = (dark_sky_table[dark_sky_table.Country == "United States"]).reset_index() #only want US

#function to get lat and long coords
def convert_location(loc):
    print(loc)
    time.sleep(2)
    geolocator = Nominatim(user_agent='Stargazing')
    #location
    location = geolocator.geocode(loc)
    if location:
        lat = location.latitude
        long = location.longitude
        return lat,long
    else:
        print(f"Location {loc} not found. Try rewording address.")
        return 0,0

#get coords
dark_sky_table_us[['lat','long']] = dark_sky_table_us['Name'].apply(lambda loc: pd.Series(convert_location(loc)))

#handle the error cases manually
dark_sky_table_us.loc[2,'lat'] = 35.3711
dark_sky_table_us.loc[2,'long'] = -111.5108
dark_sky_table_us.loc[18,'lat'] = 37.7658
dark_sky_table_us.loc[18,'long'] = -105.6236
dark_sky_table_us.loc[21,'lat'] = 37.9970
dark_sky_table_us.loc[21,'long'] = -107.2918
dark_sky_table_us.loc[28,'lat'] = 44.00015
dark_sky_table_us.loc[28,'long'] = -114.83389
dark_sky_table_us.loc[31,'lat'] = 41.23082
dark_sky_table_us.loc[31,'long'] = -86.10523
dark_sky_table_us.loc[32,'lat'] = 45.553649
dark_sky_table_us.loc[32,'long'] = -69.32452
dark_sky_table_us.loc[34,'lat'] = 45.64615
dark_sky_table_us.loc[34,'long'] = -85.55310
dark_sky_table_us.loc[35,'lat'] = 41.89758
dark_sky_table_us.loc[35,'long'] = -85.85749
dark_sky_table_us.loc[37,'lat'] = 47.45999
dark_sky_table_us.loc[37,'long'] = -87.90996
dark_sky_table_us.loc[70,'lat'] = 29.939694
dark_sky_table_us.loc[70,'long'] = -100.970206
dark_sky_table_us.loc[72,'lat'] = 30.4951
dark_sky_table_us.loc[72,'long'] = -98.8200
dark_sky_table_us.loc[75,'lat'] = 30.18852
dark_sky_table_us.loc[75,'long'] = -99.27447
dark_sky_table_us.loc[84,'lat'] = 38.5776
dark_sky_table_us.loc[84,'long'] = -112.3349

#output the dataframe to csv for later use
dark_sky_table_us.to_csv('dark_sites_us.csv',index=False)

print(dark_sky_table_us)