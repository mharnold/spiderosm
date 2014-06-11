'''
Fetch latest Oregon OSM data and generate a Portland area Path Network from it.
'''

import datetime
import json
import os
import pdb

import centerline
import config
import geo
import misc
import shp2geojson
import osm
import pnwk
import spatialite

# CONFIG
# can be overwritten in config.spiderosm.py files
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
    portland_bbox = (7604005.67,651319.12,7696978.42,732248.02)
    conf['project_bbox'] = geo.buffer_box(portland_bbox,5280) # buffer by 1 mi
    #scott_bbox = (7659144.46916011, 652983.6364829391, 7704883.335301831, 711749.7037401646)
    #conf['project_bbox'] = geo.buffer_box(scott_bbox,5280) # buffer by 1 mi

    #database
    # if not set toFalse, write results (and intermediate files) to this database
    #conf['db'] = False
    #conf['db'] = postgis.Pgis(conf['project'])
    conf['db'] = spatialite.Slite(os.path.join('data','portland','portland.sqlite'))

    config.read_config_files()

    conf['project_projection'] = geo.Projection(conf['project_proj4text'])
    setup_paths(conf['gis_data_dir'],conf['out_dir'])

    print 'project_bbox:', conf['project_bbox']

paths = {}
def setup_paths(gis_data_dir, out_dir):
    #OSM DATA
    # geofabrik extracts updated daily
    paths['osm_url'] ='http://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf'
    paths['osm'] = os.path.join(gis_data_dir, 'osm', 'oregon-latest.osm.pbf')
    paths['osm_network'] = os.path.join(out_dir,'osm') # .pnwk.geojson

def doit():
    conf = config.settings

    setup()
    log('TOP')

    # OUTPUT DIR
    if not os.path.exists(conf['out_dir']): os.makedirs(conf['out_dir'])

    misc.update_file_from_url(filename=paths['osm'], url=paths['osm_url'])
    build_osm_network(clip_rect=conf['project_bbox'],target_proj=conf['project_proj4text'])

    log('DONE')

def log(msg):
    conf = config.settings
    now = str(datetime.datetime.now())
    print now,conf['project'],msg

def build_osm_network(clip_rect=None,target_proj=None):
    conf = config.settings
    db = conf['db']

    log('building OSM network...')
    osm_data = osm.OSMData(paths['osm'], clip_rect=clip_rect, target_proj=target_proj)
    osm_data.write_geojson(paths['osm_network']) # .osm.geojson
    if db: 
        db.write_geo(osm_data,'osm_ways',geometry_type='LineString')
        db.write_geo(osm_data,'osm_nodes',geometry_type='Point')
    osm_nwk = osm_data.create_path_network()
    osm_nwk.writeGeojson(paths['osm_network']) # .pnwk.geojson
    if db: 
        db.write_pnwk(osm_nwk)
    log('building OSM network DONE.')

#doit
doit()

