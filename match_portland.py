'''
Match Portland Oregon  RLIS street centerline to OSM

'''
import os

import spiderosm.centerline
import spiderosm.config
import spiderosm.geo
import spiderosm.match
#import spiderosm.postgis
#import spiderosm.spatialite

def match_city():
    project = 'portland'

    # allow out_dir and gis_data_dir and project_bbox to be set in config files
    # DATA DIRS
    conf = spiderosm.config.settings
    conf['gis_data_dir'] = 'data'
    conf['out_dir'] = os.path.join('data',project)

    #BOUNDING BOX
    #if bbox set to None, city data bounding box plus a buffer is used.
    # approximately portland city boundary, with 1 mile buffer.
    portland_bbox = (7604005.67,651319.12,7696978.42,732248.02)
    conf['bbox'] = spiderosm.geo.buffer_box(portland_bbox,5280) # buffer by 1 mi

    spiderosm.config.read_config_files()

    gis_data_dir = conf['gis_data_dir']
    out_dir = conf['out_dir']
    bbox = conf['bbox']

    print 'gis_data_dir=%s out_dir=%s' % (gis_data_dir,out_dir)
    print 'bbox:', bbox 

    m = spiderosm.match.Match(
            project=project,
            #NAD_1983_HARN_StatePlane_Oregon_North_FIPS_3601_Feet_Intl
            #http://spatialreference.org/ref/sr-org/6856/
            proj4text = '+proj=lcc +lat_1=44.33333333333334 +lat_2=46 +lat_0=43.66666666666666 +lon_0=-120.5 +x_0=2500000 +y_0=0 +datum=NAD83 +units=ft +no_defs',
            units='feet',
            bbox=bbox,
            #db = spiderosm.postgis.PGIS(project),
            #db = spiderosm.spatialite.Slite(os.path.join(out_dir, project + '.sqlite')),
            out_dir=out_dir)

    # CITY DATA (RLIS street data)
    # source: http://rlisdiscovery.oregonmetro.gov/?resourceID=99
    # (No automatic download: go to site manually and download.)
    m.city_shp= os.path.join(gis_data_dir,'centerline','rlis','streets','streets.shp')
    m.city_geojson = os.path.join(out_dir,'streets.geojson')
    m.centerline_to_pnwk = spiderosm.centerline.rlis_pnwk
    m.city_network = os.path.join(out_dir,'city') # .pnwk.geojson

    #OSM DATA
    #geofabrik extracts updated daily
    m.osm_url = 'http://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf'
    m.osm = os.path.join(gis_data_dir, 'osm', 'geofabrik.de', 'oregon-latest.osm.pbf')
    m.osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson

    #OSM BASE (before name fixes)
    #m.base_url = 'http://download.geofabrik.de/north-america/us/oregon-140901.osm.pbf'
    #m.base = os.path.join(gis_data_dir,'osm','geofabrik.de','oregon-140901.osm.pbf')
    #m.base_network = os.path.join(out_dir,'base') # .pnwk.geojson

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()
    #m.names_osm_vs_base()

#doit
if __name__ == "__main__":
    match_city()

