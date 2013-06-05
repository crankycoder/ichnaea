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
import random

from matplotlib import pyplot, colors
from shapely.geometry import Point, MultiPoint
from descartes.patch import PolygonPatch


_PICKED = []

def plot_coords(ax, ob, color=None, char='o'):
    if color is None:
        color = random.choice(colors.cnames.values())
        while color in _PICKED:
            color = random.choice(colors.cnames.values())
        _PICKED.append(color)

    x, y = ob.xy
    ax.plot(x, y, char, color=color, zorder=1, label=ob.id, markersize=12)


fig = pyplot.figure(1, figsize=(10, 10), dpi=90)   #figsize=SIZE, dpi=90)


class Location(Point):
    def __init__(self, id, lon, lat, ss=100):
        Point.__init__(self, lon, lat)
        self.id = id
        self.lon, self.lat = lon, lat
        self.neighbours = []
        self.ss = 100

    def add_neighbour(self, neighbour):
        self.neighbours.append(neighbour)

    @classmethod
    def from_point(cls, point, label=''):
        return cls(label, point.x, point.y)


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
        selection = MultiPoint(found)
        return (Location.from_point(selection.centroid, 'guess'),
                selection.envelope)


# i am here, here's what I see.
ax = fig.add_subplot(1, 1, 1)
my_real_location = lon, lat = 23.4, 45.6

# what I see around me
cell_tower = Location('cell tower', lon + 1.4, lat + 3.2, 20)
wifi_3 = Location('wifi 1', lon + 1.8, lat - 1.8, 30)
wifi_2 = Location('wifi 2', lon - 2.3, lat + 0.9, 15)
wifi_4 = Location('wifi 3', lon - 2.1, lat + 1.9, 15)
wifi_1 = Location('wifi 4', lon - 0.2, lat - 0.4, 30)


# my exact location
my_place = Location('Exact location', lon, lat, 18.)
plot_coords(ax, my_place, 'red', char='v')

for loc in (cell_tower, wifi_3, wifi_2, wifi_1, wifi_4):
    my_place.add_neighbour(loc)
    plot_coords(ax, loc)


# crowdsourcing it
db = LocDB()
db.crowdsource(my_place)

# what I see around me, and I don't have my location
guess, envelope = db.findme(cell_tower, wifi_3, wifi_2)
plot_coords(ax, guess, 'green', char='^')

patch = PolygonPatch(envelope, facecolor='blue',
        edgecolor='black', alpha=0.2, zorder=2)
ax.add_patch(patch)

handles, labels = ax.get_legend_handles_labels()


# reverse the order
ax.legend(handles[::-1], labels[::-1])

handles2 = []
labels2 = []

for handle, label in zip(handles, labels):
    if 'wifi' in label:
        continue
    handles2.append(handle)
    labels2.append(label)
ax.legend(handles2, labels2, loc=3)

pyplot.show()
