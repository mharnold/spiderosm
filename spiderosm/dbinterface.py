import geojson

import colspecs
import geo


class DatabaseInterface(object):
    ''' Base class for postgis, and spatiallite database interfaces'''

    def __init__(self, db_name, srid=None, verbose=True):
        self.db_name = db_name
        if not srid:  srid = 4326 # default to WGS84 longlat
        self.srid = srid
        self.verbose = verbose
        if self.verbose: print 'Connecting to database %s' % db_name
        (self.con, self.cur) = self._connect()
        self._add_spatial_extension()


    def _connect(self):
        print 'DatabaseInterface._connect() stub: specialize for postgis, spatialite etc.'

    def _add_spatial_extension(self):
        print 'DatabaseInterface._add_spatial_extension() stub: specialize for postgis, spatialite etc.'

    # '%s' in pycopg2, '?' in pyspatialite
    _interpolation_ref = 'string used to reference values to be interpolated into sql string by cursor' 

    def code_point(self,point,srid=None):
        if not srid: srid=self.srid
	return "ST_GeomFromText('%s',%d)" % (geo.wkt_point(point), srid)

    def code_linestring(self,points,srid=None):
        if not srid: srid=self.srid
	return "ST_GeomFromText('%s',%d)" % (geo.wkt_linestring(points), srid)

    # NOTE: transactions are initiated automatically (by default)
    def commit(self):
	self.con.commit()

    def close(self):
	self.commit()
	self.con.close()

    # values are interpolated into s, similar to "format % values", but quoted/escaped properly for sql
    # important to use this rather than '%' or '+' for security:  sql injection attacks!
    def exec_sql(self,s,values=None):
	if values:
		self.cur.execute(s,values)
	else:
		self.cur.execute(s)

    # exec sql and return results
    def exec_sql_r(self,s,values=None):
	'''exec sql and return resulting table'''
	self.exec_sql(s, values)
	return self.cur.fetchall()

    def select(self,cols,table,where=None):
	''' make common sql 'SELECT' a tad less cumbersome'''
	parms = {'cols':cols, 'table':table, 'where':where}
	if where:
		return self.exec_sql_r("SELECT %(cols)s FROM %(table)s WHERE %(where)s" % parms)
	else:
		return self.exec_sql_r("SELECT %(cols)s FROM %(table)s" % parms)

    def get_table(self,table):
	rows = self.select('*',table);
	return rows

    def get_table_names(self):
        rows = self.select('table_name','information_schema.tables')
        return [ row[0] for row in rows ]
    
    def get_num_rows(self,table):
	rows = self.exec_sql_r('select count(*) as count from %s' % table)
	assert len(rows)==1 
        #print 'DEBUG rows', rows
	return rows[0]['count']

    def add_column(self,table,name,type='text'):
        self.exec_sql('ALTER TABLE %(table)s ADD COLUMN "%(name)s" %(type)s;' % 
                {'table':table, 'name':name, 'type':type})

    def add_geometry_column(self,table,name,type,srid=None):
        if not srid: srid = self.srid
        #print 'DEB add_geometry_column',table,name,type
        self.exec_sql('''
                SELECT AddGeometryColumn('%(table)s', '%(name)s', %(srid)d, '%(type)s', 2) 
                ''' % {'table':table, 'name':name, 'srid':srid, 'type':type})  
        #self._create_spatial_index(table,name)
                                
    def create_table(self, table, col_specs):
        col_specs = colspecs.fix(col_specs)
        self.exec_sql('DROP TABLE IF EXISTS %s' % table)

        data_specs = []  
        geom_specs = []
        for col,typ,prop in col_specs:
            if typ=='LINESTRING' or typ=='POINT':
                geom_specs.append((col,typ,prop))
            else:
                data_specs.append((col,typ,prop))
        spec_str = [ '"%s" %s' % spec[:2] for spec in data_specs ]
        spec_str = ', '.join(spec_str)

        self.exec_sql('CREATE TABLE %s (%s)' % (table, spec_str))

        # add geometry column(s)
        for col_name, col_type, parm_name in geom_specs:
            self.add_geometry_column(table,col_name,col_type)

    def write_row(self, table, col_specs, row, srid=None):
        if not srid: srid=self.srid
        col_specs = colspecs.fix(col_specs)

        def code_value(col_name, col_type, value, ref):
            if col_type == 'POINT':
                return (self.code_point(value,srid),None)
            if col_type == 'LINESTRING':
                return (self.code_linestring(value,srid),None)
            if col_type == 'TEXT':
                if not isinstance(value,basestring): value = str(value)
                return (ref, value)
            return (ref, value)

        # create row dictionary
        if isinstance(row,dict):
            rowd = row.copy()
        else:
            # is this even used?
            assert len(row) == len(col_specs)
            rowd = {}
            for i in range(len(col_specs)): rowd[col_specs[i][2]] = row[i]

        # col and value list strings
        columns = []
        values = []
        parms = []
        for col_name,col_type,prop_name in col_specs:
            if not prop_name in rowd.keys(): continue
            value = rowd[prop_name]
            if value == None: continue
            columns.append( '"' + col_name + '"')
            (value,parm) = code_value(col_name, col_type, value, self._interpolation_ref)
            values.append(value)
            if parm!=None: parms.append(parm)
            
        columns = ','.join(columns)
        values = ','.join(values)

        # create sql template for row
        sql_template  = ''' 
                    INSERT INTO %(table)s 
		        (%(columns)s)
                    VALUES
		        (%(values)s);
                    ''' % {
                        'table':table,
                        'columns':columns,
                        'values': values
                        }

        # and execute sql
        #print 'sql_template:', sql_template
        self.exec_sql(sql_template,parms)

    def write_table(self, table, col_specs, rows):
        self.create_table(table, col_specs)

        for row in rows:
            self.write_row(table, col_specs, row)
            
    def write_geo(self, geo, table_name, srid=None, geometry_type=None, col_specs=None):
        try: geo = geo.__geo_interface__
        except AttributeError: pass
        if not geometry_type: geometry_type = geo['features'][0]['geometry']['type']
        if not col_specs: col_specs = colspecs.gen(geo, geometry_type)

        #filter features for correct geometry_type
        rows = []
        for feature in geo['features']:
            if feature['geometry']['type'] != geometry_type: continue
            row = {}
            row.update(feature['properties'])
            row['geometry'] = feature['geometry']['coordinates']
            rows.append(row)
        #print 'DEBUG rows', rows

        # write the table
        self.write_table(table_name, col_specs, rows)
        self.commit()

    def write_pnwk(self, pnwk, name=None):
        if not name: name = pnwk.name
        self.write_geo(pnwk, name+'_pnwk_segs', geometry_type='LineString')
        self.write_geo(pnwk, name+'_pnwk_jcts', geometry_type='Point')

    def add_spatial_ref_sys(self, srs_info):
        existing = self.select(
            '*',
            'spatial_ref_sys',
            where='srid=%(srid)s'% srs_info
            )
        assert len(existing) <2
        if len(existing) == 1:
            e = existing[0]
            match = True
            for col in e.keys():
                if e[col] != srs_info[col]:
                    match = False
            if not match:
                msg = 'spatial ref entry for srid=%d already exists and differs!' % srs_info['srid']
                print 'dbinterface.py WARNING:', msg
        else:
            assert len(existing) == 0
            print 'dbinterface.py:', 'Adding spatial reference system (srid=%d) to postgis database %s' % (
                srs_info['srid'],
                db_name)
            colspecs = [ (col,'generic') for col in ('srid','auth_name','auth_srid','proj4text','srtext')]
            write_row('spatial_ref_sys', colspecs, srs_info)
            commit()

    def test(self,verbose=True):
        ref = (self._interpolation_ref,)
	self.exec_sql('drop table if exists test_db')
        self.exec_sql('create table test_db ("a:f1" text, other integer, test_key serial primary key)')
        self.exec_sql('insert into test_db ("a:f1", other) values (%s, %s)' % (ref*2), 
                ('''foo's"''', 1))
        self.exec_sql('''insert into test_db ("a:f1", other) values ('bar', 5)''')
        self.exec_sql('''insert into test_db ("a:f1") values ('zar')''')
	table = self.get_table('test_db')

	assert len(table)==3
	assert table[1]['other']==5
        assert table[2]['a:f1']=='zar'
	assert len(table) == self.get_num_rows('test_db')
        col_names = self.get_column_names('test_db')
        assert col_names == ['a:f1', 'other', 'test_key']
        # another way to get col_names (but in random order)
        assert len(table[0].keys()) == 3

        #add_geometry_column
        self.add_geometry_column('test_db','geometry','POINT')
        assert self.get_column_names('test_db') == ['a:f1', 'other', 'test_key', 'geometry']

        # write_table        
        col_specs = [('id', 'BIGINT'), ('a:name', 'TEXT'), ('length', 'FLOAT'), ('geometry', 'POINT')]
        rows = []
        rows.append({ 'id':1, 'a:name':'dianna', 'length':5.3})
        rows.append({ 'id':2, 'a:name':'nathan'})
        rows.append([3,'michael',5.10, (-122.0, 38.0)])
        rows.append({ 'id':4, 'a:name':None, 'length':100 })

        self.write_table('test_db2', col_specs, rows)

        assert  self.get_column_names('test_db2') == ['id', 'a:name', 'length', 'geometry']

        rowsr = self.get_table('test_db2')
        assert len(rowsr) == 4
        assert rowsr[0]['a:name'] == 'dianna'
        assert rowsr[2]['id'] == 3
        assert rowsr[1]['length'] == None

        # geo
        geometry = geojson.Point((-122.0,38.0))
        ls = geojson.LineString([(-122,38),(-122,39)])
        features = [
            geojson.Feature(geometry=geometry, id=1, properties={'name':'john','addr':1212, 'gpa':3.5}),
            geojson.Feature(geometry=geometry, id=2, properties={'fish':'salmon', 'addr':'sea', 'gpa':3, 'foo':None}),
            geojson.Feature(geometry=ls, id=10, properties={'other':10}),
            geojson.Feature(geometry=geometry, id=3, properties={'num':2**40}),
            geojson.Feature(geometry=geometry, id=4, properties={'Num':2}),
            geojson.Feature(geometry=geometry, id=5, properties={'NUM':'many'})
            ]
        geo = geojson.FeatureCollection(features)
        
        #write_geo
        self.write_geo(geo, 'test_segs', geometry_type='LineString')
        self.write_geo(geo, 'test_jcts', geometry_type='Point')
        
        # table_names
        table_names = self.get_table_names()

        #print 'table_names:',table_names
        assert 'test_db' in table_names

        # check for spatial extension
        assert 'spatial_ref_sys' in self.get_table_names()

        # check for srid
        rows = self.select('*','spatial_ref_sys','srid=%d'%self.srid)
        assert len(rows) == 1
      
        self.commit()

def test():
    print 'dbinterface PASS'

#doit
test()
