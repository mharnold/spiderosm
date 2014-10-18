'''
Match Berkeley street centerline to OSM
'''
import os
import pdb

import spiderosm.centerline
import spiderosm.config
import spiderosm.match
#import spiderosm.postgis
#import spiderosm.spatialite

def match_city():
    project = 'berkeley'

    # allow out_dir and gis_data_dir to be set in config files
    conf = config.settings
    conf['gis_data_dir'] = 'data'
    conf['out_dir'] = os.path.join('data',project)
    config.read_config_files()
    gis_data_dir = conf['gis_data_dir']
    out_dir = conf['out_dir']
    print 'gis_data_dir=%s out_dir=%s' % (gis_data_dir,out_dir)

    m = match.Match(
            project=project,
            proj4text='+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            units='meters',
            #db = spiderosm.postgis.PGIS(project)
            #db = spiderosm.spatialite.Slite(os.path.join(out_dir, project + '.sqlite'))
            out_dir=out_dir)

    #CITY DATA
    # source: http://www.ci.berkeley.ca.us/datacatalog/
    m.city_url = 'http://www.ci.berkeley.ca.us/uploadedFiles/IT/GIS/streets.zip'
    m.city_zip = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.zip')
    m.city_shp = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.shp')
    m.city_geojson = os.path.join(out_dir,'streets.geojson')
    m.centerline_to_pnwk = centerline.berkeley_pnwk
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
if __name__ == "__main__":
    match_city()

