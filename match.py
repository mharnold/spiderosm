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
import misc
import osm
import pnwk
import shp2geojson

class Match(object):
    def __init__(self, 
            project, 
            proj4text,
            units=None,
            bbox=None,
            out_dir=None,
            db = None):

        # defaults 
        if not out_dir: out_dir = 'data'
        if not units: units = 'meters'

        # properties
        self.project = project
        self.proj4text = proj4text
        self.units = units
        self.bbox = bbox
        self.out_dir = out_dir
        self.db = db;

        # city pnwk gen func
        self.city_centerline_to_pnwk = centerline.berkeley_pnwk        

        # city paths
        self.city_url = None
        self.city_zip = None
        self.city_shp = None
        self.city_geojson = None
        self.city_network = None # .pnwk.geojson

        # osm paths
        self.osm_url = None
        self.osm = None
        self.osm_network = None

        # base paths (osm base version)
        self.base_url = None
        self.base = None
        self.base_network = None

        self.log_current_task = None       
        # setup
        self.projection = geo.Projection(proj4text)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

    def log(self,msg):
        now = str(datetime.datetime.now())
        task = self.log_current_task
        if not task: task=''

        print "=====",now,self.project,task,msg

    def log_begin_task(self,msg):
        assert not self.log_current_task
        self.log_current_task = msg
        self.log('...')

    def log_end_task(self):
        assert self.log_current_task
        self.log('DONE.')
        self.log_current_task = None
        
    def fetch_city_data(self):
        self.log_begin_task('fetching city data')
        if self.city_url:
            if self.city_zip:
                download_filename = self.city_zip
            else:
                download_filename = self.city_shp
            misc.update_file_from_url(download_filename, url=self.city_url)
        if self.city_zip:
            misc.unzip(self.city_zip)
        self.log_end_task()

    def fetch_osm_data(self):
        self.log_begin_task('fetching OSM data')
        if self.osm_url:
            misc.update_file_from_url(self.osm, url=self.osm_url)
        self.log_end_task()

    def fetch_base_data(self):
        self.log_begin_task('fetching OSM base data')
        if self.base_url:
            misc.update_file_from_url(self.base, url=self.base_url)
        self.log_end_task()

    def build_city_network(self):
        self.log_begin_task('building city network')
        # shp -> geojson
        if self.city_shp:
            shp2geojson.shp2geojson(self.city_shp, self.city_geojson, clip_rect=self.bbox)

        # geojson -> pnwk
        if self.city_geojson:
            with open(self.city_geojson) as f:
                city_geojson = geojson.load(f) 
            city_nwk = self.centerline_to_pnwk(name='city', features=city_geojson['features'], clip_rect=self.bbox)
            city_nwk.write_geojson(self.city_network) 
            if self.db: self.db.write_pnwk(city_nwk)
        self.log_end_task()

    def set_bbox_from_city(self):
        assert not self.bbox
        if not self.city_network: return
        self.log_begin_task('setting bbox from city network')
       
        city_nwk = pnwk.PNwk(name='city',filename=self.city_network,units=self.units)
        city_bbox = city_nwk.get_bbox()
        print 'city_bbox:', city_bbox

        # buffer
        if self.units == 'meters':
            city_bbox_buffered = geo.buffer_box(city_bbox,1000) #buffer by 1000 meters
        else:
            assert self.units == 'feet'
            city_bbox_buffered = geo.buffer_box(city_bbox,300) #buffer by 100 yards
        print 'bbox (city bbox with buffer):', city_bbox_buffered
        self.bbox = city_bbox_buffered

        #city_bbox_buffered_geo = conf['project_projection'].project_box(city_bbox_buffered, rev=True)
        #print 'city_bbox_buffered_geo:', city_bbox_buffered_geo
        self.log_end_task()

    def set_bbox_from_osm(self):
        assert not self.bbox
        if not self.osm_network: return
        self.log_begin_task('setting bbox from osm network')
       
        osm_nwk = pnwk.PNwk(name='osm',filename=self.osm_network,units=self.units)
        osm_bbox = osm_nwk.get_bbox()
        print 'osm_bbox:', osm_bbox

        # buffer
        if self.units == 'meters':
            osm_bbox_buffered = geo.buffer_box(osm_bbox,1000) #buffer by 1000 meters
        else:
            assert self.units == 'feet'
            osm_bbox_buffered = geo.buffer_box(osm_bbox,300) #buffer by 100 yards
        print 'bbox (osm bbox with buffer):', osm_bbox_buffered
        self.bbox = osm_bbox_buffered

        #city_bbox_buffered_geo = conf['project_projection'].project_box(city_bbox_buffered, rev=True)
        #print 'city_bbox_buffered_geo:', city_bbox_buffered_geo
        self.log_end_task()


    def build_osm_pnwk(self, name, in_fname, out_fname):
        if not in_fname: return

        # osm -> geojson
        osm_data = osm.OSMData(in_fname, clip_rect=self.bbox, target_proj=self.proj4text)
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
        city_nwk = pnwk.PNwk(filename=self.city_network, name='city',units=self.units)
        osm_nwk = pnwk.PNwk(filename=self.osm_network, name='osm',units=self.units)
        self.match_pnwks(osm_nwk, city_nwk)
        self.log_end_task()

    def match_osm_to_base(self):
        if not self.osm_network: return
        if not self.base_network: return
        self.log_begin_task('matching osm to base network')
        base_nwk = pnwk.PNwk(filename=self.base_network, name='base',units=self.units)
        osm_nwk = pnwk.PNwk(filename=self.osm_network, name='osm',units=self.units)
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
                units = self.units)
        except IOError:
            self.log('Could not read osm_matched network, skipping mismatched_name_report')
            return

        self.log_begin_task('generating mismatched names report (.csv and .geojson)')

        # find mismatches
        mismatches = geofeatures.filter_features(osm_matched, 
                feature_func=mismatchFunc, 
                geom_type='LineString')
        print '%d (RAW) NAME MISMATCHES' % len(mismatches)

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
        self.projection.project_geo_features(webmap,rev=True)
        
        # write out geojson for webmap
        geo = geojson.FeatureCollection(webmap)
        fname = os.path.join(self.out_dir,'name_mismatches.geojson')
        with open(fname, 'w') as f:
            geojson.dump(geo,f,indent=2,sort_keys=True)

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
        print '%d UNIQUE NAME MISMATCHES' % count
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
                units = self.units)
        except IOError:
            self.log('Could not read osm_osm2base matched network, skipping fixed (OSM) names report')
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
        geo = geojson.FeatureCollection(webmap)
        fname = os.path.join(self.out_dir,'name_fixes.geojson')
        with open(fname, 'w') as f:
            geojson.dump(geo,f,indent=2,sort_keys=True)

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

def _test_ucb_sw1(out_dir):
    project = 'ucb_sw'
    test_data_dir = config.settings['spiderosm_test_data_dir']
    #print 'DEB test_data_dir:',test_data_dir
    in_dir = os.path.join(test_data_dir,'input',project)
    
    m = Match(
            project=project,
            proj4text='+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            units='meters',
            out_dir=out_dir)

    #CITY DATA
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

def test_ucb_sw():
    tmp_dir = tempfile.gettempdir()
    out_dir = os.path.join(tmp_dir,'ucb_sw')
    if os.path.exists(out_dir): shutil.rmtree(out_dir)
    try:
        _test_ucb_sw1(out_dir=out_dir)
    finally:
        if os.path.exists(out_dir): shutil.rmtree(out_dir)

def test():
    test_ucb_sw()
    print 'match PASS'
   
#doit
if __name__ == '__main__':
    config.read_config_files()
    test()
