#!/usr/bin/env python
'''
Match Berkeley street centerline to OSM
'''
import os
import pdb

import spiderosm.centerline
import spiderosm.config
import spiderosm.log
import spiderosm.match

def _match_city():
    global spiderosm

    project = 'berkeley'
    gis_data_dir = spiderosm.config.settings.get('gis_data_dir', 'data')
    out_dir = spiderosm.config.settings.get('out_dir', os.path.join('data',project))
    spiderosm.log.info('gis_data_dir=%s out_dir=%s', gis_data_dir, out_dir)

    # make sure out_dir exists
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    # if a database is enabled write output to it too
    if  spiderosm.config.settings.get('postgis_enabled'):
        import spiderosm.postgis
        db_name = spiderosm.config.settings.get('postgis_dbname', project)
        db = spiderosm.postgis.PGIS(db_name)
        spiderosm.log.info('Results will be written to postgis database %s', project)
    elif spiderosm.config.settings.get('spatialite_enabled'):
        import spiderosm.spatialite
        sqlite_fn = os.path.join(out_dir, project + '.sqlite')
        db = spiderosm.spatialite.Slite(sqlite_fn)
        spiderosm.log.info('Results will be written to spatialite database %s', sqlite_fn)
    else:
        db = None
       
    m = spiderosm.match.Match(
            project=project,
            proj4text='+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            units='meters',
            db=db,
            out_dir=out_dir)

    #CITY DATA (jurisdictional centerline data)
    # source: http://www.ci.berkeley.ca.us/datacatalog/
    m.city_url = 'http://www.ci.berkeley.ca.us/uploadedFiles/IT/GIS/streets.zip'
    m.city_zip = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.zip')
    m.city_shp = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.shp')
    m.city_geojson = os.path.join(out_dir,'streets.geojson')
    m.centerline_to_pnwk = spiderosm.centerline.berkeley_pnwk
    m.city_network = os.path.join(out_dir,'city') # .pnwk.geojson

    #OSM DATA (downloaded via overpass API by default)
    #geofabrik extracts updated daily
    #m.osm_url = 'http://download.geofabrik.de/north-america/us/california-latest.osm.pbf'
    #m.osm = os.path.join(gis_data_dir,'osm','geofabrik.de','california-latest.osm.pbf')
    #m.osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson

    #OSM BASE (before name fixes)
    #m.base = os.path.join(gis_data_dir,'osm','geofabrik.de','california-140401.osm.pbf')
    #m.base_network = os.path.join(out_dir,'base') # .pnwk.geojson

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()
    #m.names_osm_vs_base()

#doit
assert __name__ == "__main__"
_match_city()
