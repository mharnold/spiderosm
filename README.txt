SpiderOSM - README.txt
======================
spiderosm.org
Michael Arnold, mha.hiker@gmail.com

LEGAL
-----

Copyright (C) 2014, Michael Arnold.  All rights reserved.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF THIRD
PARTY RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN
THIS NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL
DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE
DATA FILES OR SOFTWARE.

DATA SOURCES HAVE LICENSE RESTRICITONS THAT MAY RESTRICT RECOMBINATION,
REPUBLISHING ETC.  THE INTERACTION OF THESE LICNESE CAN BE COMPLICATED!  FOR
EXAMPLE OSM AND RLIS TERMS OF USE APPEAR INCOMPATIBLE AT THIS TIME (JUNE 2014.)
LICENSES MAY BE COMPLICATED.  IT IS YOUR RESPONSIBILITY TO KNOW AND ABIDE BY 
LICENSE RESTIRCTIONS OF ANY DATA YOU MAKE USE OF.

THIS RELEASE
-----------------
VERY EARLY BETA!
Sys admin and programming skills are neeed to successfully install and use
this version of spiderOSM.

INSTALLING AND RUNNING
----------------------
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
% pip install pyshp
% pip install geojson
% pip install imposm
% pip install pylev
% pip install Shapely

(For windows, instructions for installing pip are at the same link given
above.)

TO RUN
------
email me. :)

Network Segment Attributes
--------------------------
TODO:  UPDATE THIS!

SEGID - Primary key. Not persistent:  relying on this to be constant between versions of the network will eventually cause tears.  Negative segId’s are assigned to new segments created by splitting existing segments during the merging process.

FROMJCTID - id of jct (node/intersection) where this segment originates.

FROMBEARING - compass bearing of segment at it's origin.  0=North, 90=East, etc.

TOJCTID - id of jct (node/intersection) where this segment terminates.

TOBEARING - compass bearing of end of segment (from point of view of end jct.)

NAME - canonicalized version of name associated with segment.  If multiple names, they are separated by semi-colons (‘;’)

WAYID - (foreign key) OSM id of way containing this segment.

LOCALID - (foreign key) localid of RLIS segment containing this segment.

MATCHID - (foreign key) segId of matched segment in other network.

MATCHREV - 1 if sense (direction) of matched segments are reversed with respect to each other: one ends where the other begins and vice-versa.  

MATCHSCORE - integer between 0 and 100 indicating confidence in segment match. 100 = extremely confident. 0 = exceedingly unlikely the match is correct.  This overall match score is obtained by combining name match, geo match, and bearing match scores.

NAMEMS - integer between 0 and 100 rating similarity of names between this and matched segment.  It is obtained from the ratio of the levenshtein edit distance to the name length.

GEOMS1 - integer between 0 and 100 rating similarity of the segment geometries based on DIVERGENCE.

GEOMS2 - integer between 0 and 100 rating similarity of segment geometries based on ratio of DIVERGENCE to the segment length. 

BEARINGMS1 - integer between 0 and 100 based on AVGBEARINGDELTA (see below.)

BEARINGMS2 - integer between 0 and 100 rating similarity of the segment bearings at the end points.

LENGTH - length of segment in feet

DIVERGENCE - approximately the largest distance in feet between this segment and the matched segment.  More accurately imagine, two people starting out at (the same) end of each segment and walking the respective segments to the other end, matching their speed so that the arrive at the end together, and checking the distance between each other at regular intervals.  The divergence is the greatest measured distance between the walkers.

AVGBEARINGDELTA - averages difference in bearing for two people walking the segments simultaneously (see DIVERGENCE above)

NAMEMISMATCH - if names for this and matched segments don’t match (exactly) this is set to canonicalized name string of matched segment.
 
POINTS - the segment geometry.

