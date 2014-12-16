''' Routines to help sort through spatial ref system mess. '''

import os.path
import sys

import log

def wkt2proj4(wkt_text):
    try:
        import osr #pip GDAL
    except:
        log.warning('Could not import osr (for wkt -> proj4txt conversion)')
        osr = None

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

def proj4_from_shapefile(shp_file):
    prj_file = prj_filename(shp_file)
    with open(prj_file, 'r') as f:
        wkt_text = f.read()
    return wkt2proj4(wkt_text)

def test():
    berkeley_wkt = '''PROJCS["WGS_1984_UTM_Zone_10N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-123.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]],VERTCS["NAVD_1988",VDATUM["WGS_1984_Geoid"],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]]'''

    berkeley_proj4text = '''+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs '''

    assert wkt2proj4(berkeley_wkt) == berkeley_proj4text

    shp_fn = os.path.join('foo','bar.shp')
    prj_fn = prj_filename(shp_fn)
    assert prj_fn.endswith('.prj')
    assert os.path.splitext(shp_fn)[0] == os.path.splitext(prj_fn)[0]

if __name__=="__main__":
    test()
