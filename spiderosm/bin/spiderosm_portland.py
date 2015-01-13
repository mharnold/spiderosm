#!/usr/bin/env python
'''
Match Portland Oregon RLIS street centerline to OSM
'''
import os

import spiderosm.centerline
import spiderosm.config
import spiderosm.geo
import spiderosm.log
import spiderosm.match

def _match_city():
    global spiderosm

    # dirs
    project = 'portland'
    gis_data_dir = spiderosm.config.settings.get('gis_data_dir', 'data')
    out_dir = spiderosm.config.settings.get('out_dir', os.path.join('data',project))
    spiderosm.log.info('gis_data_dir=%s out_dir=%s', gis_data_dir, out_dir)
    
    # bounding box
    # if bbox set to None, city data bounding box plus a buffer is used.
    # approximately portland city boundary, with 1 mile buffer.
    portland_bbox = (7604005.67,651319.12,7696978.42,732248.02)
    bbox = spiderosm.geo.buffer_box(portland_bbox,5280) # buffer by 1 mi
    spiderosm.log.info('gis_data_dir=%s out_dir=%s\n  bbox: %s' % (gis_data_dir, out_dir, str(bbox)))
    
    # spatial reference system
    #NAD_1983_HARN_StatePlane_Oregon_North_FIPS_3601_Feet_Intl
    srs = spiderosm.spatialref.SRS(
            url="http://www.spatialreference.org/ref/sr-org/6856/",
            units='feet',
            # proj4text missing at url as of 12/27/2014
            proj4text = '+proj=lcc +lat_1=44.33333333333334 +lat_2=46 +lat_0=43.66666666666666 +lon_0=-120.5 +x_0=2500000 +y_0=0 +datum=NAD83 +units=ft +no_defs',
            spatialite_srid=spiderosm.config.settings.get('spatialite_srid'),
            postgis_srid=spiderosm.config.settings.get('postgis_srid')
            )
    spiderosm.log.info('srs info:\n%s', srs.info())

    # make sure out_dir exists
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    # if a database is enabled write output to it too
    if  spiderosm.config.settings.get('postgis_enabled'):
        import spiderosm.postgis
        db_name = spiderosm.config.settings.get('postgis_dbname') or project
        db = spiderosm.postgis.PGIS(db_name, srs=srs)
        spiderosm.log.info('Results will be written to postgis database %s', db_name)
    elif spiderosm.config.settings.get('spatialite_enabled'):
        import spiderosm.spatialite
        sqlite_fn = os.path.join(out_dir, project + '.sqlite')
        db = spiderosm.spatialite.Slite(sqlite_fn, srs=srs)
        spiderosm.log.info('Results will be written to spatialite database %s', sqlite_fn)
    else:
        db = None

    m = spiderosm.match.Match(
            project=project,
            srs=srs,
            bbox=bbox,
            db=db,
            out_dir=out_dir,

            # CITY DATA (RLIS street data)
            # source: http://rlisdiscovery.oregonmetro.gov/?resourceID=99
            # (No automatic download: go to site manually and download.)
            city_shp= os.path.join(gis_data_dir,'centerline','rlis','streets','streets.shp'),
            city_geojson = os.path.join(out_dir,'streets.geojson'),
            centerline_to_pnwk = spiderosm.centerline.rlis_pnwk
            #UNCOMMENT NEXT LINE TO USE CUSTOMIZED centerline -> pnwk CODE: FURTHER DOWN IN THIS FILE. 
            #centerline_to_pnwk = _city_pnwk,
            #city_network = os.path.join(out_dir,'city'), # .pnwk.geojson

            #OSM DATA (downloaded via overpass API by default)
            #geofabrik extracts updated daily
            #osm_url = 'http://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf',
            #osm = os.path.join(gis_data_dir, 'osm', 'geofabrik.de', 'oregon-latest.osm.pbf'),
            #osm_network = os.path.join(out_dir,'osm'), # .pnwk.geojson

            #OSM BASE (before name fixes)
            #base_url = 'http://download.geofabrik.de/north-america/us/oregon-140901.osm.pbf',
            #base = os.path.join(gis_data_dir,'osm','geofabrik.de','oregon-140901.osm.pbf'),
            #base_network = os.path.join(out_dir,'base') # .pnwk.geojson
            )

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()
    #m.names_osm_vs_base()

# centerline data -> pnwk
# If you customize this code, be sure to uncomment:
# "m.centerline_to_pnwk = _city_pnwk" in _match_city() above.
# ALSO SEE _city_pnwk() in spiderosm_berkeley.py for an example of FEATURE FILTERING.
def _city_pnwk(features,name=None,props=None,quiet=False,clip_rect=None):
    def rlis_names(feature):
        def _rlis_names0(prefix,street_name,ftype):
            #print 'DEBUG _rlis_names0 prefix,street_name,ftype', prefix,street_name,ftype

            if not street_name or street_name=='UNNAMED': return []
            names = []

            # <prefix> <street_name> <ftype>
            name = ''
            if prefix: name += (prefix + ' ')
            name += street_name
            if ftype: name += (' ' + ftype)
            names.append(name)

            # split out names in RAMPs
            if ftype == 'RAMP':
                for sname in street_name.split('-'):
                    names += _rlis_names0(prefix,sname,'')
                    names += _rlis_names0('',sname,'')  # want 'I205' not 'NE I205'
            
            #print 'DEBUG _rlis_names0 names', names 
            return names
        properties = feature['properties']
        prefix = properties.get('PREFIX')
        street_name = properties.get('STREETNAME')
        ftype = properties.get('FTYPE')
        return _rlis_names0(prefix,street_name,ftype)
    return spiderosm.centerline.make_pnwk(features,
            props=props,
            namesFunc=rlis_names,
            name=name,
            quiet=quiet,
            clip_rect=clip_rect)

#doit
assert __name__ == "__main__"
_match_city()

