'''
interface to spatialite
'''

import os
import pdb
import tempfile

import pyspatialite
import pyspatialite.dbapi2 
import dbinterface

class Slite(dbinterface.DatabaseInterface):
    def __init__(self, dbName, verbose=True):
        super(Slite,self).__init__(dbName, verbose=verbose)        

    # establish database connection 
    def _connect(self):
	con = pyspatialite.dbapi2.connect(self.db_name)
        con.row_factory = dict_factory
	cur = con.cursor()
	return [con, cur]

    def _add_spatial_extension(self):
        if not 'spatial_ref_sys' in self.get_table_names():
            if self.verbose:
                print 'SELECT spatialite.py:','Initializing spatialite metadata for %s' % self.db_name
            self.exec_sql('select InitSpatialMetadata()')
            self.commit()
        assert 'spatial_ref_sys' in self.get_table_names()

    _interpolation_ref = '?'

    def get_column_names(self, table):
        rows = self.exec_sql_r("PRAGMA table_info(%s)" % table)
        return[row['name'] for row in rows]

    def get_table_names(self):
        rows = self.exec_sql_r("select name from main.sqlite_master WHERE type='table'")
        return [ row['name'] for row in rows ]

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

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
    # test is slow for some reason, so only run when invoked as main.
    test()
