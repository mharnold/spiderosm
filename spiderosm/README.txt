SpiderOSM - README.txt

Home Page:  http://spiderosm.org
Author:  Michael Arnold, mha@spiderosm.org
Discussion Group:  https://groups.google.com/forum/#!forum/spiderosm
Source Repository:  https://github.com/mharnold/spiderosm

SpiderOSM is a python package for matching path (street) networks, e.g. OpenStreetMaps
with government centerline data.  SpiderOSM is in early BETA.  Both sys
admin and programming skills are necessary to install and use the software at
this time.

LEGAL
=====
SpiderOSM is open software, distributed under the MIT license. 
See LICENSE.txt for details

In addition, please note:

DATA SOURCES HAVE LICENSE RESTRICITONS THAT MAY RESTRICT RECOMBINATION,
REPUBLISHING ETC.  THE INTERACTION OF THESE LICENSES CAN BE COMPLICATED!  
IT IS YOUR RESPONSIBILITY TO KNOW AND ABIDE BY LICENSE RESTIRCTIONS OF ANY DATA 
YOU MAKE USE OF.


EXAMPLES
========

bin/spider_test.py
------------------
Try this first!  It runs fairly extensive tests of all the spiderOSM modules,
does not require download of any data, and takes less than a minute to run.

bin/spider_berkeley.py
----------------------
Downloads Berkeley centerline and the latest OSM California extract, clips OSM to
(buffered) extent of Berkeley centerline data, generates path networks for
both and matches them.  Also generates mismatched name report (.csv) and
geojson file.   

By default all output/intermediary files are written as geojson only.
If postgis is enabled output will also be output to postgis ('berkeley'
database.)  If spatialite is enabled (and postgis isn't) an sqlite database
file will be output too.  (See the CONFIG section below for how-to enable
postgis and spatialite)

This takes about 15 minutes to run on my machine, plus a few minutes to
download the California OSM extract.  If Postgis or Spatialite is enabled it
will take longer.

bin/spider_portland.py
----------------------
NOTE:  default bounding box is approximately Portland proper (not the RLIS data
extent.)
Requires manual download of RLIS streets layer (centerline) data.
Downloads latest Oregon OSM extract.
Generates path networks for RLIS (city) data and OSM data, and matches them.
Also generates mismatched name report (.csv) and geojson file.
By default all output/intermediary files are written as geojson only.
If postgis is enabled output will also be output to postgis ('portland'
database.)  If spatialite is enabled (and postgis isn't) an sqlite database
file will be output too.  (See the CONFIG section below for how-to enable
postgis and spatialite)

This takes about 30 minutes to run on my machine, plus a few minutes to
download the Oregon OSM extract.  If Postgis or Spatialite is enabled it
will take longer.


DATA FORMATS
============

GeoJson (.geojson)
------------------
Geojson is the primary data format used by the matcher.  Geojson is simple and
flexible as well as human readable and even editable. Geojson is an emerging
standard, supported by many tools including Leaflet, GDAL, QGIS, and ESRI ArcGIS.  
In my experience QGIS is very slow on Geojson files: consider PostGIS and
Spatialite formats below.

PostGIS and Spatialite
----------------------
In addition to GeoJson results can be output to PostGIS and Spatialite.  
PostGIS requires a running Postgres server.  Spatialite is a file based
database system (no separate server required.)  QGIS is highly optimized for
PostGIS.  QGIS also is more efficient on Spatialite than GeoJson files.

Shapefiles (.shp)
-----------------
The ubiquious shapefile format can be imported via the included
shp2geojson.py  This version does not directly support shapefile output,
though this will likely be added in the future.  

OSM (.osm.xml and .osm.pdf)
---------------------------
Import of OSM data is supported via the imposm parser (osm.py)


COORDINATE REFERENCE SYSTEMS
============================
CRS information is not currently determined from input files, and there is no
automatic translation.  Input files should be in a locally appropriate
projection.  OSM data is translated from latlon to the local projection by the
code in osm.py  See the example toplevels (spider_berkeley.py and
spider_portland_pnwk.py) for how to setup projection information.


Path Networks (.pnwk.geojson):
=============================
The core library does comparisons on "Path Networks"  A path network
is composed of explicit segments (with associated LineString geo data) and
explicit jcts (with associated Point geo data.)  A segment has associated From and To jcts.
Segments are (directly) connected if and only if they share a common junction.
In order to match two networks, the networks must first be converted to path network
format.  Path networks for OSM data can be generated with osm.py  Path Networks
for Berkeley or RLIS centerline data can be generated with centerline.py
Customization for import of other centerline data is hopefully straight
forward.


INSTALLATION
============
All the instructions below are from a command prompt (Terminal app)
'%' indicates the shell prompt
'>>>' indicates the python prompt.

You will need Python 2.7  Versions 2.5 or 2.6 might work. Version 3.x won't
work.  To find out what version you are running:

% python --version 

If you are on Windows.  Here is how to update your Python (and also install pip which you will need
below): 

 http://docs.python-guide.org/en/latest/starting/install/win/

Install the packages spiderosm depends on with the python installer (pip)
% pip install pyproj
% pip install numpy
% pip install shapely
  shapely requires geos library, on Mac: "%brew install geos"  
% pip install pylev
% pip install geojson
% pip install imposm
  imposm loads psycopg2 (postgis interface!
  imposm needs protobuf / protoc, on Mac: "%brew install protobuf --with-python"
  impost needs tokyo-cabinet, on Mac: "%brew install tokyo-cabinet"
% pip install pyspatialite
  if trouble with this - spiderosm will install fine, but you will not be able
  to output in spaitialite formate.
% pip install pyshp
  for importing shapefiles

(For windows, instructions for installing pip are at the same link given
above.)
Additional packages are probably needed.  These will be 'announced' to you when
they are found missing at run time.

If you haven't done so already, download spiderosm from the github
repository (https://github.com/mharnold/spiderosm)
and copy it to your Python site-packages directory.
To find the location of your site-packages directory, try the following

% python
>>> import sys
>>> sys.path

Alternately add the directory containing spiderosm/ to your PYTHONPATH
environment variable.

Run spiderosm/bin/spider_test.py to check the installation:

%python spiderosm/bin/spider_test.py

This should take less than a minute to run and the final line of output should
look something like this:

"Congratulations!  SpiderOSM appears to be properly installed and functioning."

For help etc, please post to the spiderosm forum early and often.  Also please post a
description of your project.  I'd like to know who my Beta users are!  
https://groups.google.com/forum/#!forum/spiderosm


CONFIG FILES AND ENABLING POSTGIS OR SPATIALITE
===============================================
The toplevels in spiderosm/bin read .spiderosm.json (alternately
config.spiderosm.json) files to give some control
over configuration.  First any .spiderosm.json in the users home directory is
readi.  Second any .spiderosm.json in the current directory at start up, is
sourced.

Here is an example .spiderosm.json file:

{
  "gis_data_dir": "/Users/me/GIS/data",
  "postgis_enabled" : true,
  "spatialite_enabled" : false 
}


USING SPIDEROSM (ONCE INSTALLED)
================================
Copy the spiderosm/bin/spider_berkeley.py top-level (or spider_portland) and modify to suit your needs.


PATH NETWORK SEGMENT ATTRIBUTES
===============================
In the examples, e.g., bin/spider_berkeley.py the networks are named 'city'
and 'osm'.  In this case network attributes have the following prefixes (namespaces):

city$ - attributes of the original city (centerline) data
osm$  - attributes of the OpenStreetMaps input data
city_pnwk$ - attributes of the path network generated for the city data.
osm_pnwk$ - attributes of the path network generated for the OSM data.
match$ - attributes assessing the similarity of matched segments, i.e., likely
	 hood that they are properly matched.

Matched segments in path networks inherit the attributes of both input
networks, e.g. both 'city' and 'osm'.

city_pnwk (osm_pnwk)
--------------------
Note that pnwk segments are derived from splitting segments in
the input data, i.e. an osm way is likely split into multiple path network
segments.

city_pnwk$from_bearing - compass bearing of segment at it's origin.  0=North, 90=East, etc.
city_pnwk$from_jct_id - id of jct (node/intersection) where this segment originates.
city_pnwk$length - segment length in feet or meters (same units as projection)
city_pnwk$match_id - id of matched segment in osm_pnwk
city_pnwk$match_rev - 1 if sense (direction) of matched segment is reversed
city_pnwk$name - canonical version of segment name(s) used for comparison with
		 other network.
city_pnwk$seg_id - id of this segment
city_pnwk$to_bearing - compass bearing of end of segment (from point of view of end jct.)
city_pnwk$to_jct_id - id of jct (node/intersection) where this segment terminates.

match$avg_bearing_delta - averages difference in bearing for two people walking the segments 
			simultaneously (see DIVERGENCE above)
match$divergence - approximately the largest distance in feet between this segment and the
		   matched segment.  More accurately imagine, two people starting out at 
		   (the same) end of each segment and walking the respective segments to 
		   the other end, matching their speed so that the arrive at the end together, 
		   and checking the distance between each other at regular intervals.  The 
		   divergence is the greatest measured distance between the walkers.
match$score - integer between 0 and 100 indicating confidence in segment match. 
	      100 = extremely confident. 0 = exceedingly unlikely the match is correct.  
	      This overall match score is obtained by combining name match, geo match, and 
	      bearing match scores.
match$score_bearing1 - integer between 0 and 100 based on match$avgBearingDelta
match$score_bearing2 - integer between 0 and 100 rating similarity of the segment 
		      bearings at the end points.
match$score_geo1 - integer between 0 and 100 rating similarity of the segment geometries based 
		  on match$divergence.
match$score_geo2 - integer between 0 and 100 rating similarity of segment geometries based on 
		  ratio of match$divergence to the segment length. 
match$score_name - integer between 0 and 100 rating similarity of names between this and matched segment. 
 		  It is obtained from the ratio of the levenshtein edit distance to the name length.

