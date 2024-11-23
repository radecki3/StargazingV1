**PURPOSE**

There are currently not many accessible and/or adequate online tools for determining the potential quality of stargazing on a given night in a given location. 

As someone who likes to stargaze, I wanted to create some easy-to-use tools for myself, and potentially others, to be able to quickly determine stargazing potential for a given night.

**METHODS**

Here, I use a combination of Python and SQL to return a rating, as well as some supplemental information, regarding stargazing potential on a given night given a particular location in the United States. 

I also use NAAO public weather data, moon cycle calculations, and dark sky calculations to accomplish this. 

This may not be the most efficient method of accomplishing this task and so, in the StargazingV2 repo, I have a second version which does the above in one Python script, without the use of SQL. 

For general use, the StargazingV2 script is best.

**FURTHER DETAILS**

To me, the most important factors are:
  1. How dark is the sky?
  2. How cloudy is the sky?
  3. What phase is the moon in?

And thus, my ratings are heavily weighted towards these factors.
      
