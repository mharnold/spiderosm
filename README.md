# Spiderosm - README.md

Home Page:  http://spiderosm.org  
Author:  Michael Arnold, mha@spiderosm.org  
Discussion Group:  https://groups.google.com/forum/#!forum/spiderosm  
Source Repository:  https://github.com/mharnold/spiderosm  
Bug Reports:  https://github.com/mharnold/spiderosm/issues

Spiderosm is a python package for matching path (street) networks, e.g. OpenStreetMaps
with government centerline data.  

Spiderosm is still in BETA.  Python programming skills are needed to use this software.

##Legal

Spiderosm is open software, distributed under the MIT license. 
See LICENSE.txt for details

In addition, please note:

DATA SOURCES HAVE LICENSE RESTRICITONS THAT MAY RESTRICT RECOMBINATION,
REPUBLISHING ETC.  THE INTERACTION OF THESE LICENSES CAN BE COMPLICATED!   
IT IS YOUR RESPONSIBILITY TO KNOW AND ABIDE BY LICENSE RESTIRCTIONS OF ANY DATA 
YOU MAKE USE OF.

## Download and Install

### System Requirements

Spiderosm is being developed under Python2.7.  Slightly older versions of
Python may also work. Python 3 is not yet supported.

### Virtualenv

The use of virtualenv is strongly encouraged.  (See
http://virtualenv.readthedocs.org/en/latest/virtualenv.html )
This will keep the install of spiderosm from conflicting with other python
applications on your system.

### Installing with Pip

```
% pip install spiderosm --upgrade
```

### Installing from Source Distribution

Download or clone from github (https://github.com/mharnold/spiderosm)
Then:

```
% cd <your-download-dir>/spiderosm
% python setup.py install 
```

### Testing the Installation

Open a new command window (so the brand new spiderosm_test, command will be
found) and enter:

```
% spiderosm_test.py
```

This should take less than a minute to run and the final line of output should
look something like this:

```
Congratulations!  Spiderosm appears to be properly installed and functioning.
``` 

### Getting Help

For help etc, please post to the spiderosm forum early and often.  Also please post a
description of your project.  I'd like to know who my Beta users are!  

https://groups.google.com/forum/#!forum/spiderosm

In addition, for questions, comments, feature requests, or bug reports, 

create a [new issue](https://github.com/mharnold/spiderosm/issues).

## Config Files and Optional Components

### Config Files

Configuration options can be set in config.spiderosm.json (alternately .spiderosm.json) files.
First any .spiderosm.json in the users home directory is read.  Second any .spiderosm.json in 
the current directory at start up, is read.

Here is an example config.spiderosm.json file:

```
{
  "gis_data_dir": "/Users/me/GIS/data",
  "postgis_enabled" : true,
  "postgis_dbname" : "pdx",
  "spatialite_enabled" : false 
}
```

### PostGIS

If *postgis_enabled* is set you will need the python package psycopg2:

```
% pip install --upgrade psycopg2
```

In addition to *postgis_enabled*, the following configuration options are supported: *postgis_dbname*, *postgis_user*, 
*postgis_password*, *postgis_host*, and *postgis_port*.


### Spatialite

If *spatialite_enabled* (see 'Config Files' above) is set you will need the python pakcage pyspatialite:

```
% pip install --upgrade pyspatialite
```

### Imposm.parser and .osm.pbf

To parse osm binary files (.osm.pbf) you will need to install imposm.parser.
Note, that this is normally not necessary as imposm.parser is not needed for
parsing .osm.xml files, and spiderosm's 'default' method of obtaining OSM data
is via the overpass API (see bin/spiderosm_berkeley.py for example.)

Imposm.parser apparently is NOT SUPPORTED ON WINDOWS.  It requires protobuf and tokyocabinet.
On a Mac these can be installed with Homebrew (http://brew.sh) as follows:

```
% brew install protobuf --with-python
% brew install tokyo-cabinet
```

Once these dependencies have been installed the imposm.parser python package
can be installed with pip:

```
% pip install --upgrade imposm.parser
```

## Examples

### bin/spiderosm_test.py

Try this first!  It runs fairly extensive tests of all the spiderosm modules,
does not require download of any data, and takes less than a minute to run.

### bin/spiderosm_berkeley.py

Downloads Berkeley centerline and OSM data for the same area (via the overpass
API), generates path networks for both and matches them.  Also generates
mismatched name report (.csv) and geojson file.   

By default all output/intermediary files are written as geojson only.
If postgis is enabled output will also be output to postgis ('berkeley'
database.)  If spatialite is enabled (and postgis isn't) an sqlite database
file will be output too.  (See the CONFIG section above for how-to enable
postgis and spatialite)

This runs in under five minutes on my machine (including download time.)
If Postgis or Spatialite is enabled it will take longer.

### bin/spiderosm_portland.py

NOTE:  The default bounding box is approximately Portland proper (not the RLIS data
extent.)
Requires manual download of RLIS streets layer (centerline) data.
Downloads OSM data via overpass API.
Generates path networks for RLIS (city) data and OSM data, and matches them.
Also generates mismatched name report (.csv) and geojson file.
By default all output/intermediary files are written as geojson only.
If postgis is enabled output will also be output to postgis ('portland'
database.)  If spatialite is enabled (and postgis isn't) an sqlite database
file will be output too.  (See the CONFIG section above for how-to enable
postgis and spatialite)

This takes about twenty minutes on my machine nearly half of that time is for the rather large 
OSM download.  If Postgis or Spatialite is enabled runtime will go up.


## Using Spiderosm (Once Installed)

Copy the spiderosm/bin/spiderosm_berkeley.py top-level (or
spiderosm_portland.py) and modify to suit your needs.


## Data Formts

### GeoJson (.geojson)

Geojson is the primary data format used by the matcher.  Geojson is simple and
flexible as well as human readable and even editable. Geojson is an emerging
standard, supported by many tools including Leaflet, GDAL, QGIS, and ESRI ArcGIS.  
In my experience QGIS is very slow on Geojson files: consider PostGIS and
Spatialite formats below.

### PostGIS and Spatialite

In addition to GeoJson results can be output to PostGIS and Spatialite.  
PostGIS requires a running Postgres server.  Spatialite is a file based
database system (no separate server required.)  QGIS is highly optimized for
PostGIS.  QGIS also is more efficient on Spatialite than GeoJson files.

### Shapefiles (.shp)

The ubiquious shapefile format can be imported via the included
shp2geojson.py  This version does not directly support shapefile output,
though this will likely be added in the future.  

### OSM (overpass API, .osm.xml, and .osm.pbf)

Import of OSM data is supported via the overpass API.
In addition .osm.xml files can be parsed by spiderosm.
OSM binary files (.osm.pbf) parsing is currently supported via the optional python package
imposm.parser (not available for windows.)

### Coordinate Reference Systems

CRS information is not currently determined from input files, and there is no
automatic translation.  Input files should be in a locally appropriate
projection.  OSM data is translated from latlon to the local projection by the
code in osm.py  See the example toplevels (spider_berkeley.py and
spider\_portland\_pnwk.py) for how to setup projection information.

## Path Networks (.pnwk.geojson)

The core library does comparisons on "Path Networks"  A path network
is composed of explicit segments (with associated LineString geo data) and
explicit jcts (with associated Point geo data.)  A segment has associated From and To jcts.
Segments are (directly) connected if and only if they share a common junction.
In order to match two networks, the networks must first be converted to path network
format.  Path networks for OSM data can be generated with osm.py  Path Networks
for Berkeley or RLIS centerline data can be generated with centerline.py
Customization for import of other centerline data is hopefully straight
forward.

### Path Network Segment Attributes

In the examples, e.g., bin/spider_berkeley.py the networks are named 'city'
and 'osm'.  In this case network attributes have the following prefixes (namespaces):

**city$** - attributes of the original city (centerline) data  
**osm$**  - attributes of the OpenStreetMaps input data  
**city\_pnwk$** - attributes of the path network generated for the city data.  
**osm\_pnwk$** - attributes of the path network generated for the OSM data.  
**match$** - attributes assessing the similarity of matched segments, i.e., likelyhood that they are properly matched.  

Matched segments in path networks inherit the attributes of both input
networks, e.g. both 'city' and 'osm'.

#### city\_pnwk (osm\_pnwk)

Note that pnwk segments are derived from splitting segments in
the input data, i.e. an osm way is likely split into multiple path network
segments.

**city\_pnwk$from\_bearing** - compass bearing of segment at it's origin.  0=North, 90=East, etc.  
**city\_pnwk$from\_jct\_id** - id of jct (node/intersection) where this segment originates.  
**city\_pnwk$length** - segment length in feet or meters (same units as projection)  
**city\_pnwk$match\_id** - id of matched segment in osm\_pnwk  
**city\_pnwk$match\_rev** - 1 if sense (direction) of matched segment is reversed  
**city\_pnwk$name** - canonical version of segment name(s) used for comparison with other network.  
**city\_pnwk$seg\_id** - id of this segment  
**city\_pnwk$to\_bearing** - compass bearing of end of segment (from point of view of end jct.)  
**city\_pnwk$to\_jct\_id** - id of jct (node/intersection) where this segment terminates.  

**match$avg\_bearing\_delta** - averages difference in bearing for two people walking the segments simultaneously (see DIVERGENCE above)  
**match$divergence** - approximately the largest distance (in meters) between this segment and the matched segment.  More accurately imagine, two people starting out at (the same) end of each segment and walking the respective segments to the other end, matching their speed so that they arrive at the end together, and checking the distance between each other at regular intervals.  The divergence is the greatest measured distance between the walkers.  
**match$score** - integer between 0 and 100 indicating confidence in segment match. 100 = extremely confident. 0 = exceedingly unlikely the match is correct.  This overall match score is obtained by combining name match, geo match, and bearing match scores.  
**match$score\_bearing1** - integer between 0 and 100 based on match$avgBearingDelta  
**match$score\_bearing2** - integer between 0 and 100 rating similarity of the segment bearings at the end points.  
**match$score\_geo1** - integer between 0 and 100 rating similarity of the segment geometries based on match$divergence.  
**match$score\_geo2** - integer between 0 and 100 rating similarity of segment geometries based on ratio of match$divergence to the segment length.   
**match$score\_name** - integer between 0 and 100 rating similarity of names between this and matched segment.  It is obtained from the ratio of the levenshtein edit distance to the name length.  

