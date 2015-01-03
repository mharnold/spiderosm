#!/usr/bin/env python

'''
Convert shapefile to geojson
'''

import sys
import itertools
import json 

import geojson
import shapefile #pip pyshp

import geofeatures
import log
import spatialref

def shp2geojson(inFilename,outFileName,clip_rect=None, srs=None):
    # read the shapefile
    reader = shapefile.Reader(inFilename)
    fields = reader.fields[1:]
    fieldNames = [field[0] for field in fields]
    #print 'fieldNames', fieldNames
    features = []
    skipped_no_points = 0
    for (sr, ss) in itertools.izip(reader.iterRecords(), reader.iterShapes()):
        if len(ss.points) == 0: 
            skipped_no_points += 1
            continue  
        atr = dict(zip(fieldNames, sr))
        geom = ss.__geo_interface__
        if not clip_rect or geofeatures.coordinates_intersect_rect_q(geom['coordinates'],clip_rect):
            #print 'DEB geom:', geom
            #features.append(dict(type='Feature', geometry=geom, properties=atr)) 
            features.append(geojson.Feature(geometry=geom, properties=atr)) 

    # log messages
    if skipped_no_points > 0:
        log.warning("Skipped %d shapes in %s because they have no geometry.", skipped_no_points, inFilename)

    # write the geojson file
    geofeatures.write_geojson(features, outFileName, srs=srs)

def test():
    print 'shp2geojson PASS'

if __name__ == '__main__':
    if len(sys.argv) == 3:
        shp2geojson(sys.argv[1],sys.argv[2])
    else:
        print >> sys.stderr, 'Usage: %s foo.shp foo.geojson' % sys.argv[0]
