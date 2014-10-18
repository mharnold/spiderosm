import copy
import numbers
import pdb

import geojson

import geo

def _geo_features(geo):
    features = geo
    try: features = geo.__geo_interface__
    except AttributeError: pass
    try: features = features['features']
    except TypeError: pass
    return features

def filter_features(features, feature_func=None, geom_type=None, col_specs=None):
    features = _geo_features(features)

    new_features = []
    for feature in features:
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

# allows for nested cooordinate lists
def coordinates_intersect_rect_q(coords, rect):
    if isinstance(coords[0][0], numbers.Number):
        return geo.points_intersect_rect_q(coords, rect)
    else:
        # nested coord lists
        for l in coords:
            if coordinates_intersect_rect_q(l, rect): return True
        return False

def _test_coordinates_intersect_rect_q():
    coords1 = [[0,0], [10,10], [20,20]]
    coords2 = [[100,100], [20,20]]
    coords_l2 = [coords1, coords2]
    assert coordinates_intersect_rect_q(coords1,[15,15,30,30])
    assert not coordinates_intersect_rect_q(coords1,[25,15,30,30])
    assert coordinates_intersect_rect_q(coords_l2,[90,90,101,101])

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

    # _geo_features()
    out = _geo_features(features)
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = _geo_features(geojson.FeatureCollection(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = _geo_features(GeoThingy(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'

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

    print 'geofeatures PASS'

#doit
test()
