'''
interface to spatialite
'''

import os
import pdb
import tempfile

import pyspatialite
import pyspatialite.dbapi2 

import config
import dbinterface
import log
import spatialref

class Slite(dbinterface.DatabaseInterface):
    def __init__(self, dbName, srid=None, srs=None, verbose=True):
        if not srid:
            srid = config.settings.get('spatialite_srid')
        if not srid and srs:
            srid = srs.spatialite_srid
        if not srid:
            srid = 4326   # longlat, ESPG:4326 

        if not srid: srid = config.settings.get('spatialite_srid')
        super(Slite,self).__init__(dbName, srid=srid, srs=srs, verbose=verbose)        

    # establish database connection 
    def _connect(self):
	con = pyspatialite.dbapi2.connect(self.db_name)
        con.row_factory = dict_factory
	cur = con.cursor()
	return [con, cur]

    def _add_spatial_extension(self):
        if not 'spatial_ref_sys' in self.get_table_names():
            if self.verbose:
                log.info('Initializing spatialite metadata for %s', self.db_name)
            self.exec_sql('select InitSpatialMetadata()')
            self.commit()
        assert 'spatial_ref_sys' in self.get_table_names()

    _interpolation_ref = '?'

    # In general, no guaranteed column order, so return alphabetically sorted
    def get_column_names(self, table):
        rows = self.exec_sql_r("PRAGMA table_info(%s)" % table)
        return sorted([row['name'] for row in rows])

    def get_table_names(self):
        rows = self.exec_sql_r("select name from main.sqlite_master WHERE type='table'")
        return [ row['name'] for row in rows ]

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def testx(fname='out.sqlite'):
    print 'DEB spatialite testx() hack.'
    if os.path.exists(fname): os.remove(fname)

    # srs
    berkeley_url = "http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/"
    srs=spatialref.SRS(url=berkeley_url)
    print 'srs:', srs

    db = Slite(fname, verbose=False, srs=srs)
    print 'db.srid:', db.srid
    print 'db.srs:', db.srs
    print 'DEB before add'
    db.add_spatial_ref_sys()
    print 'DEB after add'

def test():
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as temp:
        fname = temp.name
    try:
        #print 'fname',fname
        db = Slite(fname, verbose=False)
        db.test(verbose=False)
    finally:
        if os.path.exists(fname): os.remove(fname)
    print "spatialite PASS"

if __name__ == "__main__":
    test()
    testx()
