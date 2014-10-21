import csv
import os
import tempfile

import geojson

def read_table(fileName):
    with open(fileName, 'rb') as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    return rows

def write(features, fileName, col_specs=None, title=None):
    with open(fileName, 'wb') as f:
        write_file(features,f,col_specs=col_specs, title=title)

def write_file(features, f, col_specs=None, title=None):
    
    # TODO auto gen col_specs from features
    assert col_specs

    writer = csv.writer(f)

    rows= []

    # title
    if title: rows.append([title])

    # columns
    cols = [spec[0] for spec in col_specs]
    rows.append(cols)

    # value rows
    for feature in features:
        props = feature['properties']
        row = [props[spec[2]] for spec in col_specs]
        rows.append(row)

    writer.writerows(rows)

def _test1(fname):
    col_specs=[('name',None,'FULLNAME'), ('CATEGORY',None,'CATEGORY')]

    features = [
    {
      "geometry": {
        "type": "LineString", 
        "coordinates": [ [10,11],[20,21] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 1, 
        "FULLNAME": "THE UPLANDS PATH", 
        "CATEGORY": "PEDESTRIAN"
      }
    },

    {
      "geometry": {
       "type": "LineString", 
        "coordinates": [ [100,110],[200,210] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 2, 
        "FULLNAME": "TRAIL", 
        "CATEGORY": "PEDESTRIAN"
      }
    },

    {
      "geometry": {
        "type": "Point", 
        "coordinates": [ 100,110 ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 10, 
        "FULLNAME": "pointy dude",
        "CATEGORY": "LIGHT, RAIL STOP"
      }
    }]

    write(features,fname, col_specs=col_specs, title='Test Table')
    rows = read_table(fname)
    #print 'rows', rows
    assert len(rows) == 5
    assert rows[0][0] == 'Test Table'
    assert rows[1] == ['name','CATEGORY']
    assert rows[4] == ['pointy dude', 'LIGHT, RAIL STOP']

def test():
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        fname = temp.name
    try:
        #print 'fname',fname
        _test1(fname)
    finally:
        if os.path.exists(fname): os.remove(fname)
    print "csvif PASS"

#doit
test()
