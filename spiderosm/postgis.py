'''
interface to postgis
'''

import pdb

import psycopg2
from psycopg2.extras import DictCursor

import config
import dbinterface
import log

class PGIS(dbinterface.DatabaseInterface):
    def __init__(self, dbName=None, user=None, password=None, host=None, port=None, srid=None, srs=None, verbose=True):
        conf = config.settings.get
        self.user = user or conf('postgis_user')
        self.password = password or conf('postgis_password')
        self.host = host or conf('postgis_host')
        self.port = port or conf('posgis_port')

        if not dbName: dbName = conf('postgis_dbname')
        assert dbName
        if not srid:
            srid = config.settings.get('postgis_srid')
        if not srid and srs:
            srid = srs.postgis_srid
        if not srid:
            srid = 4326   # longlat, ESPG:4326 

        super(PGIS,self).__init__(dbName, srid=srid, srs=srs, verbose=verbose)        

    # establish database connection 
    # NOTE: postgres server must be running and database must already exist 
    # Initial database creation (from shell prompt):
    #   % createdb <db_name>
    def _connect(self):
	con = psycopg2.connect(database=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port)
	cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
	return [con, cur]

    def _add_spatial_extension(self):
        if not 'spatial_ref_sys' in self.get_table_names():
            if self.verbose: 
                log.info('Adding postgis extension to postgres database %s',self.db_name)
            self.exec_sql('create extension postgis;')
            self.commit()
        assert 'spatial_ref_sys' in self.get_table_names()

    _interpolation_ref = '%s'

    # order of column names not guaranteed, so return sorted alphabetically
    def get_column_names(self,table):
       name_per_row = self.select('column_name', 
                 'information_schema.columns',
                  where="table_name='%s'"%table)
       col_names=[]
       for row in name_per_row: col_names.append(row[0])
       return sorted(col_names)

    def get_table_names(self):
        rows = self.select('table_name','information_schema.tables')
        return [ row[0] for row in rows ]

def test():
    # requires preexisting spaitially enabled database:
    # %createdb <dbname>
    db_name = config.settings.get('postgis_dbname','spiderosm_test')
    if not db_name: db_name = 'spiderosm_test'
    pgis = PGIS(db_name, srid=4326, verbose=False)
   
    # run tests
    pgis.test(verbose=False)

    print "postgis PASS"

# on module load
if __name__ == "__main__":
    test()

