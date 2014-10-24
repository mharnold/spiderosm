'''
interface to postgis
'''

import pdb

import psycopg2
from psycopg2.extras import DictCursor

import dbinterface

class PGIS(dbinterface.DatabaseInterface):
    def __init__(self, dbName, verbose=True):
        super(PGIS,self).__init__(dbName, verbose=verbose)        

    # establish database connection 
    # NOTE: postgres server must be running and database must already exist 
    # Initial database creation (from shell prompt):
    #   % createdb <db_name>
    def _connect(self):
	con = psycopg2.connect(database=self.db_name)
	cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
	return [con, cur]

    def _add_spatial_extension(self):
        if not 'spatial_ref_sys' in self.get_table_names():
            if self.verbose: 
                print 'pgis.py:','Adding postgis extension to postgres database %s' % self.db_name
            self.exec_sql('create extension postgis;')
            self.commit()
        assert 'spatial_ref_sys' in self.get_table_names()

    _interpolation_ref = '%s'

    def get_column_names(self,table):
       name_per_row = self.select('column_name', 
                 'information_schema.columns',
                  where="table_name='%s'"%table)
       col_names=[]
       for row in name_per_row: col_names.append(row[0])
       return col_names

    def get_table_names(self):
        rows = self.select('table_name','information_schema.tables')
        return [ row[0] for row in rows ]

def test():
    # requires preexisting spaitially enabled 'test' database:
    # %createdb test
    pgis = PGIS('test', verbose=False)
   
    # run tests
    pgis.test(verbose=False)

    print "postgis PASS"

# on module load
test()

