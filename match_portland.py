'''
Match Portland Oregon, RLIS street centerline to OSM

'''

import cgi
import datetime
import json
import os
import pdb

import geojson

import centerline
import config
import csvif
import geo
import geofeatures
import misc
import osm
import pnwk
import postgis
import shp2geojson
#import spatialite

# CONFIG
# can be overwritten in config files (e.g. ./config.spiderosm.json)
def setup():
    conf = config.settings

    conf['project'] = 'portland'
    #NAD_1983_HARN_StatePlane_Oregon_North_FIPS_3601_Feet_Intl
    #http://spatialreference.org/ref/sr-org/6856/
    conf['project_proj4text'] = '+proj=lcc +lat_1=44.33333333333334 +lat_2=46 +lat_0=43.66666666666666 +lon_0=-120.5 +x_0=2500000 +y_0=0 +datum=NAD83 +units=ft +no_defs'
    conf['gis_data_dir'] = 'data'
    conf['out_dir'] = os.path.join('data','portland')

    #BBOX
    # approximately portland city boundary, with 1 mile buffer.
    #portland_bbox = (7604005.67,651319.12,7696978.42,732248.02)
    #conf['project_bbox'] = geo.buffer_box(portland_bbox,5280) # buffer by 1 mi
    #scott_bbox = (7659144.46916011, 652983.6364829391, 7704883.335301831, 711749.7037401646)
    #conf['project_bbox'] = geo.buffer_box(scott_bbox,5280) # buffer by 1 mi
    # Using RLIS bbox plus buffer.

    config.read_config_files()
    conf['project_projection'] = geo.Projection(conf['project_proj4text'])
    setup_paths(conf['gis_data_dir'],conf['out_dir'])
    #print 'project_bbox:', conf['project_bbox']


# FILE PATHS
paths = {}
def setup_paths(gis_data_dir, out_dir):
    # RLIS street data
    # source: http://rlisdiscovery.oregonmetro.gov/?resourceID=99
    # (No automatic download: go to site manually and download.)
    paths['city_shp'] = os.path.join(gis_data_dir,'centerline','rlis','streets','streets.shp')
    paths['city_geojson'] = os.path.join(out_dir,'streets.geojson')
    paths['city_network'] = os.path.join(out_dir,'city') # .pnwk.geojson

    #OSM DATA
    # geofabrik extracts updated daily
    paths['osm_url'] ='http://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf'
    paths['osm'] = os.path.join(gis_data_dir, 'osm', 'geofabrik.de', 'oregon-latest.osm.pbf')
    paths['osm_network'] = os.path.join(out_dir,'osm') # .pnwk.geojson

def match_portland():
    conf = config.settings

    city_nwk = None
    osm_nwk = None
    setup()

    log('TOP')

    # OUTPUT DIR
    if not os.path.exists(conf['out_dir']): os.makedirs(conf['out_dir'])

    #DATABASE
    # if set write results (and intermediate files) to this database
    global db
    #db=False
    db = postgis.PGIS(conf['project'])
    #db = spatialite.Slite(os.path.join(out_dir, conf['project'] + '.sqlite'))

    # CITY 
    if True: 
        # Manual download of RLIS data required.
        build_city_network()
    
    # OSM
    if True:
        # DOWNLOAD UP-TO-DATE OSM DATA
        misc.update_file_from_url(filename=paths['osm'],url=paths['osm_url'])

        # BBOX 
        city_nwk = pnwk.PNwk(name='city',filename=paths['city_network'],units='feet')
        city_bbox = city_nwk.get_bbox()
        print 'city_bbox:', city_bbox
        city_bbox_buffered = geo.buffer_box(city_bbox,3281) #buffer by 1000 meters = 3281 feet
        print 'city_bbox_buffered:', city_bbox_buffered
        city_bbox_buffered_geo = conf['project_projection'].project_box(city_bbox_buffered, rev=True)
        print 'city_bbox_buffered_geo:', city_bbox_buffered_geo

        build_osm_network(clip_rect=city_bbox_buffered,target_proj=conf['project_proj4text'])

    # MATCH
    if True:
        if not city_nwk:
            city_nwk = pnwk.PNwk(name='city',filename=paths['city_network'],units='feet')
        if not osm_nwk: 
            osm_nwk = pnwk.PNwk(filename=paths['osm_network'],name='osm',units='feet')
        match_networks(osm_nwk, city_nwk)
    
    # MISMATCHED NAMES REPORT
    if True:
        mismatched_names_report()

    log('DONE.')

def log(msg):
    conf = config.settings
    now = str(datetime.datetime.now())
    print now,conf['project'],msg

def build_city_network():
    # CENTERLINE 
    log('building city centerline network...')
    #print prjinfo.prjinfo(city_shp_filename) need .prj extenion.
    shp2geojson.shp2geojson(paths['city_shp'], paths['city_geojson'])
    json_file = open(paths['city_geojson'])
    city_geojson = json.load(json_file) 
    json_file.close()
    city_nwk = centerline.rlis_pnwk(name='city',features=city_geojson['features'])
    city_nwk.write_geojson(paths['city_network']) 
    if db: db.write_pnwk(city_nwk)
    log('building city centerline network... DONE')

def build_osm_network(clip_rect=None,target_proj=None):
    log('building OSM network...')
    osm_data = osm.OSMData(paths['osm'], clip_rect=clip_rect, target_proj=target_proj)
    osm_data.write_geojson(paths['osm_network']) # .osm.geojson
    if db: 
        db.write_geo(osm_data,'osm_ways',geometry_type='LineString')
        db.write_geo(osm_data,'osm_nodes',geometry_type='Point')
    osm_nwk = osm_data.create_path_network(name='osm')
    osm_nwk.write_geojson(paths['osm_network']) # .pnwk.geojson
    if db: 
        db.write_pnwk(osm_nwk)
    log('DONE building OSM network.')

def match_networks(pnwk1, pnwk2):
    conf = config.settings

    log('matching %s and %s networks...' % (pnwk1.name, pnwk2.name))
    pnwk1.match(pnwk2)
    pnwk1.match_stats()
    pnwk2.match_stats()
    pnwk1.write_geojson(os.path.join(conf['out_dir'], pnwk1.name + '_matched'))
    pnwk2.write_geojson(os.path.join(conf['out_dir'], pnwk2.name + '_matched'))
    if db:
        db.write_pnwk(pnwk1, name=pnwk1.name + '_matched')
        db.write_pnwk(pnwk2, name=pnwk2.name + '_matched')
    log('DONE matching %s and %s networks.' % (pnwk1.name, pnwk2.name))

def mismatched_names_report():
    conf = config.settings

    def mismatchFunc(feature,props):
        if props.get('match$score',0)<50: return False
        if props.get('match$score_name',100)==100: return False
        if 'osm$verified:name' in props: return False
        if props.get('osm$source:name'): return False
        props['report$wayURL'] = 'http://www.openstreetmap.org/way/%d' % props['osm$way_id']
        return True

    log('generating mismatched name report...')

    # read in matched network
    osm_matched = pnwk.PNwk(
            filename=os.path.join(conf['out_dir'], 'osm_matched'),
            name = 'osm',
            units = 'feet')

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
            ('fixme', 'TEXT', 'osm$fixme:name')
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
    conf['project_projection'].project_geo_features(webmap,rev=True)
    
    # write out geojson for webmap
    geo = geojson.FeatureCollection(webmap)
    fname = os.path.join(conf['out_dir'],'name_mismatches.geojson')
    with open(fname, 'w') as f:
        #geojson.dump(webmap,f,indent=2,sort_keys=True)
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
    title = 'Berkeley area name mismatches between city centerline and OSM (dateGenerated: %s)'  
    title = title % misc.date_ymdhms()

    csv_specs= [
            ('osm', 'TEXT', 'osm_pnwk$name'),
            ('city', 'TEXT', 'city_pnwk$name'),
            ('way', 'TEXT', 'report$wayURL')
            ]

    csvif.write(unique, os.path.join(conf['out_dir'],'name_mismatches.csv'), 
            col_specs=csv_specs,
            title=title)

    log('generating mismatched name report. DONE.')

#doit
match_portland()

