#install necessary packages
import subprocess
import sys

#required packages
required_packages = ['warnings','requests','datetime','ephem','skyfield','pandas','math','matplotlib','geopy','rich','astropy']

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