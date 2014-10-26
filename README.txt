Spiderosm - README.txt

Home Page:  http://spiderosm.org
Author:  Michael Arnold, mha@spiderosm.org
Discussion Group:  https://groups.google.com/forum/#!forum/spiderosm
Source Repository:  https://github.com/mharnold/spiderosm

Spiderosm is a python package for matching path (street) networks, e.g. OpenStreetMaps
with government centerline data.  

Spiderosm is still in BETA.  Python programming skills are needed to use this
software.


LEGAL
=====
Spiderosm is open software, distributed under the MIT license. 
See LICENSE.txt for details

In addition, please note:

DATA SOURCES HAVE LICENSE RESTRICITONS THAT MAY RESTRICT RECOMBINATION,
REPUBLISHING ETC.  THE INTERACTION OF THESE LICENSES CAN BE COMPLICATED!  
IT IS YOUR RESPONSIBILITY TO KNOW AND ABIDE BY LICENSE RESTIRCTIONS OF ANY DATA 
YOU MAKE USE OF.


DOWNLOAD AND INSTALLATION
=========================

System Requirements
-------------------
Current Mac (OS X) and Linux systems should work fine.
THE WINDOWS OPERATING SYSTEM IS CURRENTLY UNSUPPORTED.  
This is because the imposm package, used to parse OpenStreetMap data files 
(.osm.pbf and .osm.xml) does not support windows.

Spiderosm is being developed under Python2.7  slightly older versions of
Python may also work. Python 3 is not yet supported.

Dependencies
------------
Spiderosm uses the python package imposm.parser to parser OpenStreetMap files
(.osm.xml and .osm.pbf)   imposm.parser requires protobuf and tokyocabinet.
On a Mac these can be installed with Homebrew (http://brew.sh) as follows:

%brew install protobuf --with-python
%brew install tokyo-cabinet

Virtualenv
----------
The use of virtualenv is strongly encouraged.  (See
http://virtualenv.readthedocs.org/en/latest/virtualenv.html )
This will keep the install of spiderosm from conflicting with other python
applications on your system.

Installing with Pip
-------------------
The easiest way to download and install is with pip.  From a shell prompt
(command window):

% pip install spiderosm --upgrade

(The '%' indicates a command prompt, you don't type it. :)

Installing from source distribution
-----------------------------------
Download or clone from github (https://github.com/mharnold/spiderosm)
From a shell prompt:

% cd <your-download-dir>/spiderosm
% python setup.py install 

Testing the installation
------------------------
Open a new command window (so the brand new spiderosm_* commands will be
found) and enter:

% spiderosm_test.py

This should take less than a minute to run and the final line of output should
look something like this:

"Congratulations!  Spiderosm appears to be properly installed and functioning."

Getting Help
------------
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

If postgis_enabled is set you will need the python package psycopg2:
% pip install --upgrade psycopg2

If spatialite_enabled is set you will need the python pakcage pyspatialite:
% pip install --upgrade pyspatialite


EXAMPLES
========

bin/spiderosm_test.py
------------------
Try this first!  It runs fairly extensive tests of all the spiderosm modules,
does not require download of any data, and takes less than a minute to run.

bin/spiderosm_berkeley.py
----------------------
Downloads Berkeley centerline and the latest OSM California extract, clips OSM to
(buffered) extent of Berkeley centerline data, generates path networks for
both and matches them.  Also generates mismatched name report (.csv) and
geojson file.   

By default all output/intermediary files are written as geojson only.
If postgis is enabled output will also be output to postgis ('berkeley'
database.)  If spatialite is enabled (and postgis isn't) an sqlite database
file will be output too.  (See the CONFIG section above for how-to enable
postgis and spatialite)

This takes about 15 minutes to run on my machine, plus a few minutes to
download the California OSM extract.  If Postgis or Spatialite is enabled it
will take longer.

bin/spiderosm_portland.py
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
file will be output too.  (See the CONFIG section above for how-to enable
postgis and spatialite)

This takes about 30 minutes to run on my machine, plus a few minutes to
download the Oregon OSM extract.  If Postgis or Spatialite is enabled it
will take longer.


USING SPIDEROSM (ONCE INSTALLED)
================================
Copy the spiderosm/bin/spiderosm_berkeley.py top-level (or
spiderosm_portland.py) and modify to suit your needs.


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

