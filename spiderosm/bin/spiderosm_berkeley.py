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
import spiderosm.spatialref

def _match_city():
    global spiderosm

    # dirs
    project = 'berkeley'
    gis_data_dir = spiderosm.config.settings.get('gis_data_dir', 'data')
    out_dir = spiderosm.config.settings.get('out_dir', os.path.join('data',project))
    spiderosm.log.info('gis_data_dir=%s out_dir=%s', gis_data_dir, out_dir)

    # spatial reference system
    srs = spiderosm.spatialref.SRS(
            url="http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/",
            units='meters',
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
        spiderosm.log.info('Results will be written to postgis database %s', project)
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
            db=db,
            out_dir=out_dir,

            #CITY DATA (jurisdictional centerline data)
            # source: http://www.ci.berkeley.ca.us/datacatalog/
            city_url = 'http://www.ci.berkeley.ca.us/uploadedFiles/IT/GIS/streets.zip',
            city_zip = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.zip'),
            city_shp = os.path.join(gis_data_dir,'centerline','berkeley','streets','streets.shp'),
            city_geojson = os.path.join(out_dir,'streets.geojson'),
            #centerline_to_pnwk = spiderosm.centerline.berkeley_pnwk
            centerline_to_pnwk = _city_pnwk,
            city_network = os.path.join(out_dir,'city') # .pnwk.geojson

            #OSM DATA (downloaded via overpass API by default)
            #geofabrik extracts updated daily
            #osm_url = 'http://download.geofabrik.de/north-america/us/california-latest.osm.pbf',
            #osm = os.path.join(gis_data_dir,'osm','geofabrik.de','california-latest.osm.pbf'),
            #osm_network = os.path.join(out_dir,'osm') # .pnwk.geojson,

            #OSM BASE (before name fixes)
            #base = os.path.join(gis_data_dir,'osm','geofabrik.de','california-140401.osm.pbf'),
            #base_network = os.path.join(out_dir,'base') # .pnwk.geojson
            )

    # do the name crosscheck (results written to out_dir)
    m.names_cross_check()
    #m.names_osm_vs_base()

# centerline data -> pnwk
def _city_pnwk(features, name=None, props=None, quiet=False, clip_rect=None):
    def berkeley_names(feature): 
        names = []
        props = feature['properties']
        cat = props['CATEGORY']
        name = props['FULLNAME']
        words = name.split(' ')
        first = words[0]
        if name=='TRAIL' and cat =='PEDESTRIAN': return names 
        if name=='RAMP' and cat == 'CONNECTOR': return names
        if name=='ALLEY': return names
        if 'UNNAMED' in name: return names
        names.append(name)

        # add unadorned freeway names.
        if cat in ('CONNECTOR','HIGHWAY') and len(words)>1 and len(first)>1 and first[0]=='I':
            try: 
                if int(first[1:]) > 0: names.append(first)
            except ValueError: pass

        # for 'HWY 13 N', add 'CA 13'
        if cat in ('CONNECTOR','HIGHWAY') and first=='HWY' and len(words)>1:
            try: 
                if int(words[1]) > 0: names.append('CA ' + words[1])
            except ValueError: pass
        return names

    def berkeley_filter(feature):
        category = feature['properties']['CATEGORY']
        return category in ('CONNECTOR','HIGHWAY','MAJOR','MINOR','PEDESTRIAN')

    return spiderosm.centerline.make_pnwk(features, 
            props=props,
            namesFunc=berkeley_names,
            filter_func=berkeley_filter,
            name=name,
            quiet=quiet,
            clip_rect=clip_rect)

#doit
assert __name__ == "__main__"
_match_city()
