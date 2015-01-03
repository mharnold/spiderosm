import codecs
import cStringIO
import csv
import os
import tempfile

import geojson

### Unicode capable wrappers for csv reader/writer (from https://docs.python.org/2/library/csv.html)

class _UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class _UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = _UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class _UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def read_table(fileName):
    with open(fileName, 'rb') as f:
        #reader = csv.reader(f)
        reader = _UnicodeReader(f)
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

    writer = _UnicodeWriter(f)

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

def _test_unicode(fname):
    col_specs=[('osm',None,'osm'), ('city',None,'city')]

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
        "CATEGORY": "PEDESTRIAN",
        "osm": u'1 VEJ',
        "city": u'HVF VED PILEG\xc5RDEN', 
      }
    }]

    write(features,fname, col_specs=col_specs, title='Unicode Test')
    rows = read_table(fname)
    #print 'rows', rows
    assert len(rows) == 3
    assert rows[0][0] == 'Unicode Test'
    assert rows[1] == ['osm','city']
    assert rows[2] == [u'1 VEJ', u'HVF VED PILEG\xc5RDEN']

def test():
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        fname = temp.name
    try:
        #print 'fname',fname
        _test1(fname)
    finally:
        if os.path.exists(fname): os.remove(fname)

    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        fname = temp.name
    try:
        _test_unicode(fname)
    finally:
        if os.path.exists(fname): os.remove(fname)

    print "csvif PASS"

#doit
if __name__ == "__main__":
    test()
