"""
This module implements all the maths.

Terms
-----

* A signal source is either a cell tower or a wifi access point

* The location db contains coordinates of cell towers or wifi access points

* a measure is a list of wifi or cell tower, each  one with a signal strength
  when possible and a unique key.

* Signal strength is generally some ASU (arbitrary strength unit) measure like
  "16" or "92" with a meaning dependent on the network standard

* Time of flight is a measure of how much time it took a signal to reach the
  user equipment, gathered from things like "round trip time" or "timing advance"

* A cell/wifi record consists of a unique id, a lat/lon location, a network
  standard, a maximum radius, a minimum and maximum signal strength and a maximum
  time of flight

Features
--------

1/ our submit API feeds the measurement DB with a list of signal sources around the device
2/ our async workers look at the measurements and the location DB and updates the location DB
3/ our search API returns an approximate location based on the location DB,
   given a list of signal sources around the device


Algorithms
----------

The location DB has for each element, if possible a REAL location and a list of
crowd-sourced locations if we don't know the real location, we define the
location as being the center of gravity [or another thing, like the center of
the intersection of all measurement radius] of all crowd-sourced locations,
given the signal strength if provided the functions for this are:

 add_close_location(element, location, accuracy, signal_strength=None,
flight_time=None)  (may create the element, record the min/max seen signal
strength and max time of flight if available, update cell radius guess)

1. UPDATE LOCATIONS FROM MEASURES

for each element in a measure
  look in the DB if we have it or it's on a blacklist for "always moving" sources
    add_close_location(element, location, accuracy, signal_strength, flight_time) if it's not present
  compute_theoretical_location(element) to know the location of the element we have
  purge old measures
  mark the location with a timestamp, update the measurement counter

2. COMPUTE THEORETICAL LOCATION

organize close locations into clusters (the ones close to each other are making a cluster)
calculate the center of gravity of the biggest cluster - that's the theoretical location
purge old measures

3. PURGE OLD MEASURES

for each location we purge the oldest ones but we keep at least 10 event if
they are old.

4. CRON

for each location which timestamps older than a month: purge old measure
"""


class LocDB(object):
    def __init__(self):
        self.locs = {}

    def crowdsource(self, loc):
        self.locs[loc.id] = loc
        for neighbour in loc.neighbours:
            self.locs[neighbour.id] = neighbour

    def findme(self, *neighbours):
        found = []
        for neighbour in neighbours:
            if neighbour.id in self.locs:
                found.append(neighbour)
        return self._gravity(found)

    def _gravity(self, locations):
        lons = [location.lon for location in locations]
        lats = [location.lat for location in locations]
        len_ = len(locations)
        return sum(lons) / len_, sum(lats) / len_


# i am here, here's what I see.
#

class Location(object):
    def __init__(self, id, lon, lat, ss=100):
        self.id = id
        self.lon, self.lat = lon, lat
        self.neighbours = []
        self.ss = 100

    def add_neighor(self, neighbour):
        self.neighbours.append(neighbour)



my_real_location = lon, lat = 23.4, 45.6

# what I see around me
cell_tower = Location(1, lon + 1.4, lat + 3.2, 20)
wifi_3 = Location(2, lon + 1.8, lat - 1.8, 30)
wifi_2 = Location(3, lon - 2.3, lat + 0.9, 15)
my_place = Location(4, lon - 1.1, lat + 1.2, 18)

for loc in (cell_tower, wifi_3, wifi_2):
    my_place.add_neighor(loc)

# crowdsourcing it
db = LocDB()
db.crowdsource(my_place)

# what I see around me, and I don't have my location
guess = db.findme(cell_tower, wifi_3, wifi_2)
print guess
