**Required Packages**

A few packages are used that are required for functionality. You can either install them yourself as below or the script will do it for you.

```
python -m pip install astropy
python -m pip install pandas
python -m pip install skyfield
python -m pip install geopy
python -m pip install ephem
python -m pip install datetime
python -m pip install requests
python -m pip install warnings
python -m pip install math
python -m pip install rich
python -m pip install matplotlib
```
**Run The Script**

Download all the files from this repo (Code --> Download ZIP) and keep in one folder. StargazingV1.py is the only thing you need to run.

```
python StargazingV1.py
```

**Purpose**

There are currently not many accessible and/or adequate online tools for determining the potential quality of stargazing on a given night in a given location. 

As someone who likes to stargaze, I wanted to create some easy-to-use tools for myself, and potentially others, to be able to quickly determine stargazing potential for a given night.

**Methods**

Here, I use Python to return ratings regarding stargazing potential on a given night given a particular location in the United States.

I also return a significant amount of supplmental info such as weather forecast, nearest dark sites, visible stars and planets, and more.

I also use location calculations, NWS public weather data, and moon cycle calculations to accomplish this.

Here, in StargazingV1, I use an API call to collect the required data, as well as a few packages.

StargazingV1 is relatively basic. I only look at 12 hour increments for weather, and some of my criteria is biased towards what I believe is good for stargazing.

In future versions, I hope to return a more comprehensive evaluation of stargazing quality, perhaps using some weather models.

**Further Details**

To me, the most important factors are:
  1. How dark is the sky?
  2. How cloudy is the sky?
  3. What phase is the moon in?

And thus, my ratings are heavily weighted towards these factors.
      
