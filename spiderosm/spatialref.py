''' Handle Spatial Reference System Specificatioo

url -  
e.g. 'http://spatialreference.org/ref/epsg/nad83-utm-zone-10n/' 
used to specify srs in geojson output files

proj4text -
e.g. '+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs'
Needed internally to reproject OSM data to planar coordinates.
Also used when specifying a new srs entry for a spatially enabled database (postgis or spatialite.)

srtext -
e.g. '+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs',
            'srtext': 'PROJCS["NAD_1983_UTM_Zone_10N",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-123],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'
Also know as wkt = well known text.  Needed to specify a new srs for a spatially enabled database (postgis or spatialite)

POSSIBLY, if the optional osr package is installed ('%pip install osr') only one of proj4text or srtext need be specified, the other will be auto derived.  THIS NEEDS TESTING.

auth_name, auth_srid
e.g.  auth_name='EPSG', auth_srid=26910
Needed when specifying a new srs entry for a spatially enabled database (postgis or spatialite.)
'''

import json
import os.path
import sys

import geojson.crs

import config
import misc
import log

# by default db srid's derived from auth_srid by adding this offset
# there is a postgis constraint that checks that srid is < 998999
DB_SRID_OFFSET = 800000

class SRS(object):
    def __init__(self,
            hint=None,
            url=None,
            auth_name=None,
            auth_srid=None,
            postgis_srid=None,
            spatialite_srid=None,
            proj4text=None,
            srtext=None,
            units=None,
            filename=None):

        # copy args to attributes
        self.hint = hint
        self.url = url
        self.auth_name = auth_name
        self.auth_srid = auth_srid
        self.postgis_srid = postgis_srid
        self.spatialite_srid = spatialite_srid
        self.proj4text = proj4text
        self.srtext = srtext
        self.units = units
        self.filename = filename

        # hint
        # TODO look for meaning in hint:  filename, 'EPSG:4326'?  proj4text? url? ...

        # if spatialireference.org url, use it!
        if self.url:
            if not self.srtext: self.srtext = misc.get_url(self.url+'esriwkt/')
            if not self.proj4text: self.proj4text = misc.get_url(self.url+'proj4/')
            if (not self.auth_name) or (not self.auth_srid):
                text = misc.get_url(self.url+'json/')
                # fixe bad json syntax on spatialref.org
                text = text.replace('\'','"')
                data = json.loads(text)
                self.auth_name = data['type']
                self.auth_srid = data['properties']['code']

        # if filename provided, use it!
        if self.filename and not self.srtext:
            self.srtext = srtext_from_shapefile(self.filename)
            
        # if osr (GDAL) is available, use it!
        import_osr()
        if osr:
            if not self.srtext and self.auth_name=='EPSG' and self.auth_srid:
                self.srtext = EPSG2wkt(self.auth_srid)
            if not self.srtext and self.proj4text: self.srtext = proj42wkt(self.proj4text)
            if not self.proj4text and self.srtext: self.proj4text = wkt2proj4(self.srtext)

        # set db srids from auth_srid
        if self.auth_srid:
            if not self.spatialite_srid: self.spatialite_srid = self.auth_srid%100000 + DB_SRID_OFFSET
            if not self.postgis_srid: self.postgis_srid = self.auth_srid%100000 + DB_SRID_OFFSET

        # default to meters
        if not self.units:
            self.units = 'meters'

    def info_attr(self,attr): 
        format = "%s: %%s\n" % attr
        return format  % self.__dict__.get(attr)

    def info(self):
        text = ""
        #text += "url: %s\n" % self.__dict__.get('url')
        for attr in ['url', 'auth_name', 'auth_srid', 'postgis_srid', 'spatialite_srid', 
                'proj4text', 'srtext', 'units']:
            text += self.info_attr(attr)

        return text

def import_osr():
    global osr

    # only try to load once
    try:
        if osr==None: return osr
    except NameError:
        pass

    try:
        import osr #pip GDAL
    except:
        log.warning("Could not import osr for spatial reference conversions:  '%pip GDAL' to install.")
        osr = None

# not working?
def EPSG2wkt(auth_srid):
    import_osr()
    if not osr: return None

    srs = osr.SpatialReference()
    if srs.ImportFromEPSG(auth_srid):
       log.warning('Could not parse EPSG auth_srid: %s', auth_srid)
       return None
    else:
        return srs.ExportToWkt()

def proj42wkt(proj4_text):
    import_osr()
    if not osr: return None

    srs = osr.SpatialReference()
    if srs.ImportFromProj4(proj4_text):
       log.warning('Could not parse proj4text spatial ref: %s', proj4_text)
       return None
    else:
        return srs.ExportToWkt()

def wkt2proj4(wkt_text):
    import_osr()
    if not osr: return None

    srs = osr.SpatialReference()
    if srs.ImportFromWkt(wkt_text):
       log.warning('Could not parse wkt spatial ref: %s', wkt_text)
       return None
    else:
        return srs.ExportToProj4()

def prj_filename(shp_filename):
    (root,ext) = os.path.splitext(shp_filename)
    return root+'.prj'

def srtext_from_shapefile(shp_file):
    prj_file = prj_filename(shp_file)
    with open(prj_file, 'r') as f:
        wkt_text = f.read()
    return wkt_text

def proj4_from_shapefile(shp_file):
    wkt_text = srtext_from_shapefile(shp_file)
    return wkt2proj4(wkt_text)

def geojson_crs(srs):
    if not srs or not srs.url: return None
    assert "spatialreference.org" in srs.url
    properties = {
            "href": srs.url + "ogcwkt/",
            "type": "ogcwkt"
            }
    return geojson.crs.Linked(properties=properties)

def test():
    import_osr()

    test_data_dir = config.settings['spiderosm_test_data_dir']

    berkeley_url="http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/"
    berkeley_auth_name = 'EPSG'
    berkeley_auth_srid = 32610
    berkeley_proj4text = '''+proj=utm +zone=10 +ellps=WGS84 +datum=WGS84 +units=m +no_defs '''
    berkeley_wkt = '''PROJCS["WGS_1984_UTM_Zone_10N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-123],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'''
    berkeley_wkt_prj_file = '''PROJCS["WGS_1984_UTM_Zone_10N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-123.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD_1988",VDATUM["WGS_1984_Geoid"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]'''
    berkeley_filename = os.path.join(test_data_dir,'input','ucb_sw','streets.shp')
    #assert wkt2proj4(berkeley_wkt) == berkeley_proj4text

    shp_fn = os.path.join('foo','bar.shp')
    prj_fn = prj_filename(shp_fn)
    assert prj_fn.endswith('.prj')
    assert os.path.splitext(shp_fn)[0] == os.path.splitext(prj_fn)[0]

    srs=SRS(proj4text=berkeley_proj4text)
    assert srs.proj4text == berkeley_proj4text
    #print srs.srtext 

    srs=SRS(filename=berkeley_filename)
    assert srs.filename == berkeley_filename
    assert srs.srtext == berkeley_wkt_prj_file
    if osr: assert srs.proj4text

    srs=SRS(auth_name=berkeley_auth_name,auth_srid=berkeley_auth_srid)
    assert srs.auth_name == berkeley_auth_name
    assert srs.auth_srid == berkeley_auth_srid
    # osr conversion from EPSG not working?
    #if osr: assert srs.proj4text == berkeley_proj4text

    srs=SRS(url=berkeley_url)
    assert srs.url == berkeley_url
    assert srs.srtext == berkeley_wkt
    assert srs.proj4text == berkeley_proj4text
    assert srs.auth_name == berkeley_auth_name
    assert srs.auth_srid == berkeley_auth_srid
    db_srid = berkeley_auth_srid + DB_SRID_OFFSET
    assert srs.spatialite_srid == db_srid
    assert srs.postgis_srid == db_srid
    #print 'geojson_crs:',geojson_crs(srs)
    assert geojson_crs(None) == None
    assert geojson_crs(srs)["type"]=="link"

    #print srs.info()
if __name__=="__main__":
    test()
