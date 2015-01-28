import copy
import json
import numbers
import pdb

import geojson

import geo
import spatialref

def geo_feature(geo):
    """extract a feature from various types of input"""
    feature = geo
    try: feature = feature.__geo_interace__
    except AttributeError: pass
    return feature

def geo_features(geo):
    """extracts a list of features, for multiple types of input"""
    features = geo
    try: features = geo.__geo_interface__
    except AttributeError: pass
    try: features = features['features']
    except TypeError: pass
    return features

def geo_feature_collection(geo, srs=None):
    """return a feature collection for multiple types of input.
    Add coordinate ref system, if srs arg given."""

    # handle geo_interface
    try: geo = geo.__geo_interface__
    except AttributeError: pass
    
    # input is already a feature collection? 
    type = None
    try: type = geo['type'] 
    except: pass
    isfc = (type=='FeatureCollection')

    if isfc:
        fc = geo
    
    else:
        features = geo_features(geo)
        fc = geojson.FeatureCollection(features)

    # add coordinate reference system, if srs supplied
    if srs:  fc.crs = spatialref.geojson_crs(srs)

    return fc

#If features are seg and node list for example, avoids memory overhead of generating 
#a full geojson representation of input.
def write_geojson(features, outFileName, srs=None):
    features = geo_features(features)

    with open(outFileName,'w') as f:
        # FeatureCollection header
        f.write('{\n"type": "FeatureCollection",\n')

        # spatial ref spec
        if srs: 
            f.write('"crs": ')
            json.dump(spatialref.geojson_crs(srs),f,indent=2)
            f.write(',\n')

        # features header
        f.write('"features": [\n')

        # features
        for feature in features:
            geojson.dump(feature,f,indent=2)
            if feature != features[-1]: f.write(',')
            f.write('\n\n')

        # close features
        f.write(']\n')

        # close FeatureCollection
        f.write('}\n')
 
def filter_features(features, feature_func=None, geom_type=None, col_specs=None, clip_rect=None):
    features = geo_features(features)

    new_features = []
    for feature in features:
        if clip_rect and not coordinates_intersect_rect_q(feature['geometry']['coordinates'], 
                clip_rect): continue
        if geom_type and feature['geometry']['type'] != geom_type: continue
        new_feature = copy.deepcopy(feature)
        if feature_func:
            # feature_func may edit feature
            if not feature_func(new_feature,new_feature['properties']): continue
        new_features.append(new_feature)

        if col_specs:
            props = new_feature['properties']
            out = {}
            for (col_name,col_type,prop_name) in col_specs:
                if prop_name in props:
                    out[col_name] = props[prop_name]
            new_feature['properties'] = out

    return new_features

def bbox(features):
    features = geo_features(features)

    bbox = geo.BBox()

    for feature in features:
        coords = feature['geometry']['coordinates']
        _add_coords_to_bbox(bbox, coords)
    return bbox.rect()

def _add_coords_to_bbox(bbox,coords):
    if isinstance(coords[0], numbers.Number):
        #single point
        bbox.add_point(coords)
    elif isinstance(coords[0][0], numbers.Number):
        #list of points
        bbox.add_points(coords)
    else:
        # nested point lists
        for l in coords:
            _add_coords_to_bbox(bbox, l)

# allows for nested cooordinate lists
def coordinates_intersect_rect_q(coords, rect):
    if isinstance(coords[0], numbers.Number):
        #single point
        return geo.points_intersect_rect_q((coords,), rect)
    elif isinstance(coords[0][0], numbers.Number):
        #list of points
        return geo.points_intersect_rect_q(coords, rect)
    else:
        # nested point lists
        for l in coords:
            if coordinates_intersect_rect_q(l, rect): return True
        return False

def _test_coordinates_intersect_rect_q():
    coords1 = [[0,0], [10,10], [20,20]]
    coords2 = [[100,100], [20,20]]
    coords_l2 = [coords1, coords2]
    coords3 = [12,50]
    assert coordinates_intersect_rect_q(coords1,[15,15,30,30])
    assert not coordinates_intersect_rect_q(coords1,[25,15,30,30])
    assert coordinates_intersect_rect_q(coords_l2,[90,90,101,101])
    assert coordinates_intersect_rect_q(coords3, [11,49,13,51])

def test():
    _test_coordinates_intersect_rect_q()
    features = [
    {
      "geometry": {
        "type": "LineString", 
        "coordinates": [ [10,11],[20,21] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 1, 
        "FULLNAME": "THE UPLANDS PATH", 
        "CATEGORY": "PEDESTRIAN"
      }
    },

    {
      "geometry": {
        "type": "LineString", 
        "coordinates": [ [100,110],[200,210] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 2, 
        "FULLNAME": "TRAIL", 
        "CATEGORY": "PEDESTRIAN"
      }
    },

    {
      "geometry": {
        "type": "Point", 
        "coordinates": [ 100,110 ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 10, 
        "FULLNAME": "pointy dude",
        "CATEGORY": "LIGHT RAIL STOP"
      }
    }]

    class GeoThingy(object):
        @property
        def __geo_interface__(self): return self.geo
        def __init__(self,features): 
            self.geo = geojson.FeatureCollection(features)

    class GeoFeatureThingy(object):
        @property
        def __geo_interface__(self): return self.geo
        def __init__(self,feature): 
            self.geo = feature

    thingys = [GeoFeatureThingy(feature) for feature in features]

    #print 'DEB writing files to test write_geojson()'
    #write_geojson(features,'foo.geojson')
    #write_geojson(thingys,'thingy.geojson')

    # geo_features()
    out = geo_features(features)
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = geo_features(geojson.FeatureCollection(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = geo_features(GeoThingy(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'

    #geo_feature_collection() 
    berkeley_url = "http://www.spatialreference.org/ref/epsg/wgs-84-utm-zone-10n/"
    srs=spatialref.SRS(url=berkeley_url)
    fc = geo_feature_collection(GeoThingy(features),srs=srs)
    assert fc['crs']['properties'] and fc['crs']['type'] 
    assert len(fc['features']) == 3
    fc = geo_feature_collection(fc)
    assert fc['crs']['properties'] and fc['crs']['type'] 
    assert len(fc['features']) == 3
    fc = geo_feature_collection(features,srs=srs)
    assert fc['crs']['properties'] and fc['crs']['type'] 
    assert len(fc['features']) == 3

    # filter_features() - trivial case
    assert len(filter_features([])) == 0
    
    # check for deep copy
    out = filter_features(features)
    assert len(out) == 3
    assert out[1]['properties']['FULLNAME'] == 'TRAIL'
    out[1]['properties']['FULLNAME'] = 'Matt Davis'
    assert features[1]['properties']['FULLNAME'] == 'TRAIL'
    assert out[1]['properties']['FULLNAME'] == 'Matt Davis'

    # geom_type
    out = filter_features(features, geom_type='Point')
    assert len(out)==1 and out[0]['geometry']['type']=='Point'

    # feature_func
    def ffunc(feature,props): 
        if not props['OBJECTID'] > 1: return False
        props['FORMAL_NAME'] = 'Ms. ' + props['FULLNAME']
        return True

    out = filter_features(features, feature_func=ffunc)
    assert len(out)==2
    assert out[0]['properties']['FORMAL_NAME'] == 'Ms. TRAIL'

    # col_specs
    specs = [('num','INT','OBJECTID'),('name','INT','FORMAL_NAME')]
    out = filter_features(features, ffunc, geom_type='LineString', col_specs=specs)
    assert len(out) == 1
    assert out[0]['properties']['name'] == 'Ms. TRAIL'

    # clip_rect
    out = filter_features(features, clip_rect= (0,0,15,15))
    assert len(out)==1
    assert out[0]['properties']['OBJECTID'] == 1

    # bbox
    assert bbox(features) == (10, 11, 200, 210)

    print 'geofeatures PASS'

#doit
if __name__=="__main__":
    test()
