import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import warnings

def light_pollution(lat,long, location):
    warnings.simplefilter(action='ignore')
    image_path = "BlackMarble_2016_3km.jpg"
    light_map = mpimg.imread(image_path)

    map_extent = [-180,180,-90,90] #[min_lon,max_lon,min_lat,max_lat]

    markers = {
        (long,lat,location) 
    }
    #gneral map settings
    plt.figure(figsize=(12,6))
    plt.imshow(light_map, extent=map_extent, aspect='auto')
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.xlim([-135,-55])  #Contintental US only
    plt.ylim([25,60])
    plt.axis('off')
    plt.subplots_adjust(left=0,right=1,top=1,bottom=0)
    #plot markets on map
    for lon, lat, label in markers:
        plt.plot(lon, lat, 'ro', markersize=8) 
        plt.text(lon + 1, lat, label, fontsize=9, color='white', bbox=dict(facecolor='black', alpha=0.5, boxstyle='round'))
    plt.show()
    return