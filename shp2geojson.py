#!/usr/bin/env python

'''
Convert shapefile to geojson
'''

import sys
import itertools
import json 

import shapefile #pip pyshp

def shp2geojson(inFilename,outFilename):
    # read the shapefile
    reader = shapefile.Reader(inFilename)
    fields = reader.fields[1:]
    fieldNames = [field[0] for field in fields]
    #print 'fieldNames', fieldNames
    features = []
    for (sr, ss) in itertools.izip(reader.iterRecords(), reader.iterShapes()):
        atr = dict(zip(fieldNames, sr))
        geom = ss.__geo_interface__
        features.append(dict(type='Feature', geometry=geom, properties=atr)) 
 
    # write the geojson file
    jsonFile = open(outFilename, 'w')
    jsonFile.write(
            json.dumps({'type':'FeatureCollection', 'features':features}, indent=2) 
            + "\n")
    jsonFile.close()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        shp2geojson(sys.argv[1],sys.argv[2])
    else:
        print >> sys.stderr, 'Usage: %s foo.shp foo.geojson' % sys.argv[0]
