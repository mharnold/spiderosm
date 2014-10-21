#!/usr/bin/env python

'''
Convert shapefile to geojson
'''

import sys
import itertools
import json 

import shapefile #pip pyshp

import geofeatures

def shp2geojson(inFilename,outFilename,clip_rect=None):
    # read the shapefile
    reader = shapefile.Reader(inFilename)
    fields = reader.fields[1:]
    fieldNames = [field[0] for field in fields]
    #print 'fieldNames', fieldNames
    features = []
    for (sr, ss) in itertools.izip(reader.iterRecords(), reader.iterShapes()):
        atr = dict(zip(fieldNames, sr))
        geom = ss.__geo_interface__
        if not clip_rect or geofeatures.coordinates_intersect_rect_q(geom['coordinates'],clip_rect):
            #print 'DEB geom:', geom
            features.append(dict(type='Feature', geometry=geom, properties=atr)) 
 
    # write the geojson file
    jsonFile = open(outFilename, 'w')
    jsonFile.write(
            json.dumps({'type':'FeatureCollection', 'features':features}, indent=2) 
            + "\n")
    jsonFile.close()

def test():
    print 'shp2geojson PASS'

if __name__ == '__main__':
    if len(sys.argv) == 3:
        shp2geojson(sys.argv[1],sys.argv[2])
    else:
        print >> sys.stderr, 'Usage: %s foo.shp foo.geojson' % sys.argv[0]
