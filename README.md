**Required Packages**

A few packages are used that are required for functionality. Make sure to install them:

```
pip install astropy pandas skyfield geopy ephem datetime requests warnings
```
**Purpose**

There are currently not many accessible and/or adequate online tools for determining the potential quality of stargazing on a given night in a given location. 

As someone who likes to stargaze, I wanted to create some easy-to-use tools for myself, and potentially others, to be able to quickly determine stargazing potential for a given night.

**Methods**

Here, I use Python to return a rating, as well as some supplemental information, regarding stargazing potential on a given night given a particular location in the United States. 

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
      
