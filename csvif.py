import csv
import geojson

def readTable(fileName):
    with open(fileName, 'rb') as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    return rows
def write(features,fileName, colSpecs=None, title=None):
    with open(fileName, 'wb') as f:
        writeFile(features,f,colSpecs=colSpecs, title=title)

def writeFile(features,f,colSpecs=None, title=None):
    
    if not colSpecs: colSpecs = fooBar
    writer = csv.writer(f)

    rows= []

    # title
    if title: rows.append([title])

    # columns
    cols = [spec[0] for spec in colSpecs]
    rows.append(cols)

    # value rows
    for feature in features:
        props = feature['properties']
        row = [props[spec[2]] for spec in colSpecs]
        rows.append(row)

    writer.writerows(rows)

def test():
    fname = 'csv_test_file.csv'
    colSpecs=[('name',None,'FULLNAME'), ('CATEGORY',None,'CATEGORY')]

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

    write(features,fname, colSpecs=colSpecs, title='Test Table')
    rows = readTable(fname)
    print 'rows', rows
    assert len(rows) == 5
    assert rows[0][0] == 'Test Table'
    assert rows[1] == ['name','CATEGORY']
    assert rows[4] == ['pointy dude', 'LIGHT, RAIL STOP']

    print 'csvif test PASSED'

#doit
test()
