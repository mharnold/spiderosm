'''
Utility class for using spiderosm to match jurisdictional (city) to (OSM) networks, generate name mismatch reports, etc.
'''

import cgi
import datetime
import json
import os
import pdb
import shutil
import tempfile

import geojson

import centerline
import config
import csvif
import geo
import geofeatures
import log
import misc
import osm
import pnwk
import shp2geojson
import spatialref

class Match(object):
    def __init__(self, 
            project, 
            srs=None,
            proj4text=None,
            units=None,
            bbox=None,
            out_dir=None,
            db=None,

            #city data (jurisdictional centerline)
            city_url=None,
            city_zip=None,
            city_shp=None,
            city_geojson=None,
            centerline_to_pnwk=None,
            city_network=None,

            #osm data (downloaded via overpass API by default)
            osm_url=None,
            osm=None,
            osm_network=None,

            #osm base (before name fixes)
            base=None,
            base_network=None
            ):

        # spatial ref - complicated (for backward compatibility)
        if srs:
            if units:
                assert srs.units == units
            elif srs.units: 
                units = srs.units
            else:
                units = 'meters'

            if proj4text:
                assert srs.proj4text == proj4text
            else:
                proj4text = srs.proj4text
        else:
            # if no srs, and no proj4text, we may be able to derive proj4text from the city shapeifle
            if not proj4text and self.city_shp: 
                proj4text = spatialref.proj4_from_shapefile(self.city_shp)

        # argument defaults 
        if not out_dir: out_dir = 'data'
        if not centerline_to_pnwk: centerline_to_pnwk = centerline.berkeley_pnwk        
        if not city_network: city_network = os.path.join(out_dir,'city') # .pnwk.geojson

        # properties
        self.project = project
        self.srs = srs
        self.proj4text = proj4text
        self.units = units
        self.bbox = bbox
        self.out_dir = out_dir
        self.db = db;

        # city 
        self.city_url = city_url
        self.city_zip = city_zip
        self.city_shp = city_shp
        self.city_geojson = city_geojson
        self.centerline_to_pnwk = centerline_to_pnwk # centerline to pnwk func
        self.city_network = city_network

        # osm paths
        self.osm_url = osm_url
        self.osm = osm
        self.osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson

        # base paths (osm base version)
        self.base_url = None
        self.base = None
        self.base_network = None

        # logging
        self.log_current_task = None       

        # projection
        if self.proj4text:
            self.projection = geo.Projection(self.proj4text)
        else:
            self.projection = None

        # checks
        if not self.proj4text:
            log.warning("Unable to determine proj4text for Match object %s\n"
                    "  (Needed to convert raw osm data to appropriate planar coordinates.)",
                    self.project)

        if not srs or not srs.url:
            log.warning("No srs.url specified for Match object %s\n"
                    "  (Needed for geojson file crs specifications.)", self.project)

        # path setup
        if not os.path.exists(self.out_dir): os.makedirs(self.out_dir)

    def log_begin_task(self,msg):
        assert not self.log_current_task
        self.log_current_task = msg
        log.info('--- BEGINNING %s ...', self.log_current_task)

    def log_end_task(self):
        assert self.log_current_task
        log.info('--- DONE %s.', self.log_current_task)
        self.log_current_task = None
        
    def fetch_city_data(self):
        if self.city_url:
            if self.city_zip:
                download_filename = self.city_zip
            else:
                download_filename = self.city_shp
            self.log_begin_task('fetching city data')
            misc.update_file_from_url(download_filename, url=self.city_url)
            self.log_end_task()
        if self.city_zip:
            misc.unzip(self.city_zip)

    def fetch_osm_data(self):
        if not self.osm_url: return
        
        self.log_begin_task('fetching OSM data')
        misc.update_file_from_url(self.osm, url=self.osm_url)
        self.log_end_task()

    def fetch_base_data(self):
        if not self.base_url: return

        self.log_begin_task('fetching OSM base data')
        misc.update_file_from_url(self.base, url=self.base_url)
        self.log_end_task()

    def build_city_network(self):
        self.log_begin_task('building city network')
        # shp -> geojson
        if self.city_shp:
            shp2geojson.shp2geojson(self.city_shp, self.city_geojson, clip_rect=self.bbox, srs=self.srs)

        # geojson -> pnwk
        if self.city_geojson:
            with open(self.city_geojson) as f:
                city_geojson = geojson.load(f) 
            city_nwk = self.centerline_to_pnwk(name='city', 
                    features=geofeatures.geo_features(city_geojson), 
                    clip_rect=self.bbox)
            city_nwk.srs = self.srs
            city_nwk.write_geojson(self.city_network) 
            if self.db: self.db.write_pnwk(city_nwk)
        self.log_end_task()

    def set_bbox_from_city(self):
        assert not self.bbox
        if not self.city_network: return
        self.log_begin_task('setting bbox from city network')
       
        city_nwk = pnwk.PNwk(name='city',filename=self.city_network,units=self.units, srs=self.srs)
        city_bbox = city_nwk.get_bbox()
        log.info('city_bbox: %s', str(city_bbox))

        # buffer
        if self.units == 'meters':
            city_bbox_buffered = geo.buffer_box(city_bbox,1000) #buffer by 1000 meters
        else:
            assert self.units == 'feet'
            city_bbox_buffered = geo.buffer_box(city_bbox,300) #buffer by 100 yards
        log.info('bbox (city bbox with buffer): %s', str(city_bbox_buffered))
        self.bbox = city_bbox_buffered

        #city_bbox_buffered_geo = conf['project_projection'].project_box(city_bbox_buffered, rev=True)
        #print 'city_bbox_buffered_geo:', city_bbox_buffered_geo
        self.log_end_task()

    def set_bbox_from_osm(self):
        assert not self.bbox
        if not self.osm_network: return
        self.log_begin_task('setting bbox from osm network')
       
        osm_nwk = pnwk.PNwk(name='osm',filename=self.osm_network,units=self.units, srs=self.srs)
        osm_bbox = osm_nwk.get_bbox()
        log.info('osm_bbox: %s', str(osm_bbox))

        # buffer
        if self.units == 'meters':
            osm_bbox_buffered = geo.buffer_box(osm_bbox,1000) #buffer by 1000 meters
        else:
            assert self.units == 'feet'
            osm_bbox_buffered = geo.buffer_box(osm_bbox,300) #buffer by 100 yards
        log.info('bbox (osm bbox with buffer): %s', str(osm_bbox_buffered))
        self.bbox = osm_bbox_buffered

        #city_bbox_buffered_geo = conf['project_projection'].project_box(city_bbox_buffered, rev=True)
        #print 'city_bbox_buffered_geo:', city_bbox_buffered_geo
        self.log_end_task()


    def build_osm_pnwk(self, name, in_fname, out_fname):
        #if in_fname None, osm.OSMData() imports data via overpass api
        #if not in_fname: return

        # osm -> geojson
        osm_data = osm.OSMData(in_fname, 
                clip_rect=self.bbox, 
                srs=self.srs,
                target_proj=self.proj4text)
        osm_data.write_geojson(out_fname) # .osm.geojson
        if self.db: 
            self.db.write_geo(osm_data, name+'_ways',geometry_type='LineString')
            self.db.write_geo(osm_data, name+'_nodes',geometry_type='Point')

        # osm -> pnwk
        osm_nwk = osm_data.create_path_network(name=name)
        osm_nwk.write_geojson(out_fname) # .pnwk.geojson
        if self.db: 
            self.db.write_pnwk(osm_nwk,name+'_nwk')

    def build_osm_network(self):
        self.log_begin_task('building OSM network')
        self.build_osm_pnwk('osm', self.osm, self.osm_network)
        self.log_end_task()
    
    def build_base_network(self):
        self.log_begin_task('building OSM base network')
        self.build_osm_pnwk('base', self.base, self.base_network)
        self.log_end_task()
        
    def match_pnwks(self, pnwk1, pnwk2, match_suffix=None):
        if not match_suffix: match_suffix = '_matched'
        pnwk1_out = pnwk1.name + match_suffix
        pnwk2_out = pnwk2.name + match_suffix

        pnwk1.match(pnwk2)
        pnwk1.match_stats()
        pnwk2.match_stats()

        pnwk1.write_geojson(os.path.join(self.out_dir, pnwk1_out))
        pnwk2.write_geojson(os.path.join(self.out_dir, pnwk2_out))
        if self.db:
            self.db.write_pnwk(pnwk1, name=pnwk1_out)
            self.db.write_pnwk(pnwk2, name=pnwk2_out)

    def match_city_to_osm(self):
        if not self.city_network: return
        if not self.osm_network: return
        self.log_begin_task('matching city to osm network')
        city_nwk = pnwk.PNwk(filename=self.city_network, name='city',units=self.units, srs=self.srs)
        osm_nwk = pnwk.PNwk(filename=self.osm_network, name='osm',units=self.units, srs=self.srs)
        self.match_pnwks(osm_nwk, city_nwk)
        self.log_end_task()

    def match_osm_to_base(self):
        if not self.osm_network: return
        if not self.base_network: return
        self.log_begin_task('matching osm to base network')
        base_nwk = pnwk.PNwk(filename=self.base_network, name='base',units=self.units, srs=self.srs)
        osm_nwk = pnwk.PNwk(filename=self.osm_network, name='osm',units=self.units, srs=self.srs)
        self.match_pnwks(osm_nwk, base_nwk, match_suffix='_osm2base')
        self.log_end_task()

    def gen_mismatched_names_report(self):
        def mismatchFunc(feature,props):
            if props.get('match$score',0)<50: return False
            if props.get('match$score_name',100)==100: return False
            props['report$osm_verified'] = str(
                    ('osm$verified:name' in props) or 
                    ('osm$source:name' in props)) 
            props['report$wayURL'] = 'http://www.openstreetmap.org/way/%d' % props['osm$way_id']
            return True

        # read in matched network
        try:
            osm_matched = pnwk.PNwk(
                filename = os.path.join(self.out_dir, 'osm_matched'),
                name = 'osm',
                units = self.units,
                srs=self.srs)
        except IOError:
            log.error('Could not read osm_matched network, skipping mismatched_name_report')
            return

        self.log_begin_task('generating mismatched names report (.csv and .geojson)')

        # find mismatches
        mismatches = geofeatures.filter_features(osm_matched, 
                feature_func=mismatchFunc, 
                geom_type='LineString')

        # filter props down for webmap
        webmap_specs= [
                ('osm', 'TEXT', 'osm_pnwk$name'),
                ('city', 'TEXT', 'city_pnwk$name'),
                ('wayId', 'BIGINT', 'osm$way_id'),
                ('fixme', 'TEXT', 'osm$fixme:name'),
                ('osmVerified', 'TEXT', 'report$osm_verified')
                ]
        webmap = geofeatures.filter_features(mismatches, 
                col_specs=webmap_specs)

        # htlml quote TEXT property values to guard against injection attacks.
        for feature in webmap:
            props = feature.properties
            for (name, t, ignore) in webmap_specs:
                if t != 'TEXT': continue
                if not name in props: continue
                props[name] = cgi.escape(props[name])

        # unproject for web map use
        if not self.projection:
            log.error("No projection specified, could not convert to lon/lat for name_mismatches.geojson")
        else:
            self.projection.project_geo_features(webmap,rev=True)
        
        # write out geojson for webmap
        fname = os.path.join(self.out_dir,'name_mismatches.geojson')
        geofeatures.write_geojson(webmap,fname)

        # make unique and sorted
        unique = []
        pairs = {}
        for feature in mismatches:
            props = feature['properties']
            pair = (props['osm_pnwk$name'], props['city_pnwk$name']) 
            if pair in pairs: continue
            unique.append(feature)
            pairs[pair] = True
        count = len(pairs)

        log.info('name mismatches: %d raw, %d unique.', len(mismatches), count)

        def keyFunc(feature):
            p=feature['properties']
            return (p['osm_pnwk$name'], p['city_pnwk$name'])
        unique.sort(key=keyFunc)

        # write csv report
        title = '%s name mismatches between city centerline and OSM (generated: %s)'  
        title = title % (self.project, misc.date_ymdhms())

        csv_specs= [
                ('osm', 'TEXT', 'osm_pnwk$name'),
                ('city', 'TEXT', 'city_pnwk$name'),
                ('way', 'TEXT', 'report$wayURL'),
                ('osmVerified', 'TEXT', 'report$osm_verified')
              ] 
        csvif.write(unique, os.path.join(self.out_dir,'name_mismatches.csv'), 
                col_specs=csv_specs,
                title=title)
        self.log_end_task()

    def gen_fixed_osm_names_report(self):
        def mismatchFunc(feature,props):
            if props.get('match$score',0)<50: return False
            if props.get('match$score_name',100)==100: return False
            if not props.get('osm$source:name'): return False
            props['report$wayURL'] = 'http://www.openstreetmap.org/way/%d' % props['osm$way_id']
            return True


        # read in matched network
        try:
            osm_matched = pnwk.PNwk(
                filename=os.path.join(self.out_dir,'osm_osm2base'),
                name = 'osm',
                units = self.units,
                srs = self.srs)
        except IOError:
            log.error('Could not read osm_osm2base matched network, skipping fixed (OSM) names report')
            return

        self.log_begin_task('generating fixed (OSM) names report (.csv and .geojson)')

        # find fixes
        fixes = geofeatures.filter_features(osm_matched, feature_func=mismatchFunc, geom_type='LineString')
        print '%d (RAW) NAME FIXES' % len(fixes)

        # filter props down for webmap
        webmap_specs= [
                ('old', 'TEXT', 'base$name'),
                ('new', 'TEXT', 'osm$name'),
                ('source','TEXT', 'osm$source:name'),
                ('wayId', 'BIGINT', 'osm$way_id')
                ]
        webmap = geofeatures.filter_features(fixes, col_specs=webmap_specs)

        # htlml quote TEXT property values to guard against injection attacks.
        for feature in webmap:
            props = feature.properties
            for (name, t, ignore) in webmap_specs:
                if t != 'TEXT': continue
                if not name in props: continue
                props[name] = cgi.escape(props[name])

        # unproject for web map use
        self.projection.project_geo_features(webmap,rev=True)
        
        # write out geojson for webmap
        fname = os.path.join(self.out_dir,'name_fixes.geojson')
        geofeatures.write_geojson(webmap,fname)

        # make unique and sorted
        unique = []
        pairs = {}
        for feature in fixes:
            props = feature['properties']
            pair = (props['osm_pnwk$name'], props['base_pnwk$name']) 
            if pair in pairs: continue
            unique.append(feature)
            pairs[pair] = True
        count = len(pairs)
        print '%d UNIQUE NAME FIXES' % count
        def keyFunc(feature):
            p=feature['properties']
            return (p['osm_pnwk$name'], p['base_pnwk$name'])
        unique.sort(key=keyFunc)
       
        # write csv report
        title = self.project + ' OSM name fixes (generated: %s)'  
        title = title % misc.date_ymdhms()

        csv_specs= [
                ('old', 'TEXT', 'base_pnwk$name'),
                ('new', 'TEXT', 'osm_pnwk$name'),
                ('way', 'TEXT', 'report$wayURL')
                ]

        csvif.write(unique, os.path.join(self.out_dir,'name_fixes.csv'), 
                col_specs=csv_specs,
                title=title)

        self.log_end_task()

    def names_cross_check(self):
        # build city network
        self.fetch_city_data()
        self.build_city_network()

        # if no bbox set, use (buffered) city bbox to clip OSM data
        if not self.bbox: self.set_bbox_from_city()

        # build OSM network
        self.fetch_osm_data()
        self.build_osm_network()

        # match networks
        self.match_city_to_osm()

        # gen mismatched names report (.csv and .geojson files)
        self.gen_mismatched_names_report()
        
    def names_osm_vs_base(self):
        # if no bbox set, use (buffered) city bbox to clip OSM data
        if not self.bbox: self.set_bbox_from_city()

        # build base network
        self.fetch_base_data()
        self.build_base_network()

        # match osm to base
        self.match_osm_to_base()

        # gen fixed osm names report (.csv and .geojson files)
        self.gen_fixed_osm_names_report()

def _test_ucb_sw1(out_dir,db=None, srs=None):
    project = 'ucb_sw'
    test_data_dir = config.settings['spiderosm_test_data_dir']
    #print 'DEB test_data_dir:',test_data_dir
    in_dir = os.path.join(test_data_dir,'input',project)

    m = Match( 
            project=project,
            srs=srs,
            out_dir=out_dir,
            db=db,

            #CITY DATA
            city_geojson = os.path.join(in_dir,'streets.geojson'),
            centerline_to_pnwk = centerline.berkeley_pnwk,
            city_network = os.path.join(out_dir,'city'), # .pnwk.geojson 
            
            #OSM DATA
            osm = os.path.join(in_dir,'ucb_sw.osm.xml'),
            osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson
            )

    m.names_cross_check()

    # check results
    names_report_file = os.path.join(out_dir,'name_mismatches.csv')
    rows = csvif.read_table(names_report_file)
    assert len(rows) == 7
    assert rows[2] == ['FRANK SCHLESSINGER WAY',
            'CROSS CAMPUS RD',
            'http://www.openstreetmap.org/way/22278224',
            'True']

def test_ucb_sw(out_dir=None):

    # srs
    berkeley_url = "http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/"
    srs=spatialref.SRS(url=berkeley_url)

    # if out_dir specified, use it, and keep it.
    if out_dir:
        if os.path.exists(out_dir): shutil.rmtree(out_dir)
        _test_ucb_sw1(out_dir=out_dir,srs=srs)
        return

    tmp_dir = tempfile.gettempdir()
    out_dir = os.path.join(tmp_dir,'ucb_sw')
    if os.path.exists(out_dir): shutil.rmtree(out_dir)
    try:
        _test_ucb_sw1(out_dir=out_dir,srs=srs)
    finally:
        if os.path.exists(out_dir): shutil.rmtree(out_dir)

def test(out_dir=None):
    test_ucb_sw(out_dir=out_dir)
    print 'match PASS'

def test_sqlite():
    print 'DEB match with sqlite'

    import spatialite
    out_dir = 'data'
    sqlite_fn = os.path.join(out_dir,'test.sqlite')
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    if os.path.isfile(sqlite_fn): os.remove(sqlite_fn)

    # srs
    berkeley_url = "http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/"
    srs=spatialref.SRS(url=berkeley_url)

    os.path

    db = spatialite.Slite(sqlite_fn,srs=srs)
    _test_ucb_sw1(out_dir=out_dir,db=db,srs=srs)

def test_postgis():
    print 'DEB match with postgis'

def test_postgis():
    print 'DEB match with postgis'
    import postgis
    db_name = config.settings.get('postgis_dbname','spiderosm_test')
    db = postgis.PGIS(db_name)
    _test_ucb_sw1(out_dir='data',db=db)

def test_derive_proj4text():
    project = 'ucb_sw'
    test_data_dir = config.settings['spiderosm_test_data_dir']
    #print 'DEB test_data_dir:',test_data_dir
    in_dir = os.path.join(test_data_dir,'input',project)
    out_dir='data'
    db=None

    m = Match(
            project=project,
            #proj4text='+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            units='meters',
            out_dir=out_dir,
            db=db)

    #CITY DATA
    gis_data_dir = config.settings.get('gis_data_dir', 'data')
    m.city_shp = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.shp')
    m.city_geojson = os.path.join(in_dir,'streets.geojson')
    m.centerline_to_pnwk = centerline.berkeley_pnwk
    m.city_network = os.path.join(out_dir,'city') # .pnwk.geojson

    #OSM DATA
    m.osm = os.path.join(in_dir,'ucb_sw.osm.xml')
    m.osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()

    # check results
    names_report_file = os.path.join(out_dir,'name_mismatches.csv')
    rows = csvif.read_table(names_report_file)
    assert len(rows) == 7
    assert rows[2] == ['FRANK SCHLESSINGER WAY',
            'CROSS CAMPUS RD',
            'http://www.openstreetmap.org/way/22278224',
            'True']
   
#doit
if __name__ == '__main__':
    test()
    #test(out_dir='out')
    #test_sqlite()
    #test_postgis()
    #test_derive_proj4text()
   

