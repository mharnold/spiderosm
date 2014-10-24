#!/usr/bin/env python
'''
Match Berkeley street centerline to OSM
'''
import os
import pdb

import spiderosm.centerline
import spiderosm.config
import spiderosm.match

def _match_city():
    global spiderosm
    project = 'berkeley'

    # allow out_dir and gis_data_dir to be set in config files (.spiderosm.json)
    conf = spiderosm.config.settings
    conf['gis_data_dir'] = 'data'
    conf['out_dir'] = os.path.join('data',project)

    spiderosm.config.read_config_files()
    print 'spiderosm.config.settings:', spiderosm.config.settings

    gis_data_dir = conf['gis_data_dir']
    out_dir = conf['out_dir']
    print 'gis_data_dir=%s out_dir=%s' % (gis_data_dir,out_dir)

    # make sure out_dir exists
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    # if a database is enabled write output to it too
    # NOTE: currently writes to only one database even if multiple databases are enabled.
    write_to_postgis = True
    write_to_spatialite = True
    db = None
    if write_to_postgis and (not db) and conf.get('postgis_enabled'):
        import spiderosm.postgis
        db = spiderosm.postgis.PGIS(project)
        print 'Results will be written to postgis database %s' % project
    if write_to_spatialite and (not db) and conf.get('spatialite_enabled'):
        import spiderosm.spatialite
        sqlite_fn = os.path.join(out_dir, project + '.sqlite')
        db = spiderosm.spatialite.Slite(sqlite_fn)
        print 'Results will be written to spatialite database %s' % sqlite_fn
       
    m = spiderosm.match.Match(
            project=project,
            proj4text='+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            units='meters',
            db=db,
            out_dir=out_dir)

    #CITY DATA
    # source: http://www.ci.berkeley.ca.us/datacatalog/
    m.city_url = 'http://www.ci.berkeley.ca.us/uploadedFiles/IT/GIS/streets.zip'
    m.city_zip = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.zip')
    m.city_shp = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.shp')
    m.city_geojson = os.path.join(out_dir,'streets.geojson')
    m.centerline_to_pnwk = spiderosm.centerline.berkeley_pnwk
    m.city_network = os.path.join(out_dir,'city') # .pnwk.geojson

    #OSM DATA
    #geofabrik extracts updated daily
    m.osm_url = 'http://download.geofabrik.de/north-america/us/california-latest.osm.pbf'
    m.osm = os.path.join(gis_data_dir,'osm','geofabrik.de','california-latest.osm.pbf')
    m.osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson

    #OSM BASE (before name fixes)
    #m.base = os.path.join(gis_data_dir,'osm','geofabrik.de','california-140401.osm.pbf')
    #m.base_network = os.path.join(out_dir,'base') # .pnwk.geojson

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()
    #m.names_osm_vs_base()

#doit
assert __name__ == "__main__"
_match_city()
