import copy
import pdb

import geojson

def geoFeatures(geo):
    features = geo
    try: features = geo.__geo_interface__
    except AttributeError: pass
    try: features = features['features']
    except TypeError: pass
    return features

# def write

def filterFeatures(features, featureFunc=None, geomType=None, colSpecs=None):
    features = geoFeatures(features)

    new_features = []
    for feature in features:
        if geomType and feature['geometry']['type'] != geomType: continue
        new_feature = copy.deepcopy(feature)
        if featureFunc:
            # featureFunc may edit feature
            if not featureFunc(new_feature,new_feature['properties']): continue
        new_features.append(new_feature)

        if colSpecs:
            props = new_feature['properties']
            out = {}
            for (col_name,col_type,prop_name) in colSpecs:
                if prop_name in props:
                    out[col_name] = props[prop_name]
            new_feature['properties'] = out

    return new_features

def test():
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

    # geoFeatures()
    out = geoFeatures(features)
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = geoFeatures(geojson.FeatureCollection(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'
    out = geoFeatures(GeoThingy(features))
    assert len(out)==3 and out[0]['type'] == 'Feature'

    # filterFeatures() - trivial case
    assert len(filterFeatures([])) == 0
    
    # check for deep copy
    out = filterFeatures(features)
    assert len(out) == 3
    assert out[1]['properties']['FULLNAME'] == 'TRAIL'
    out[1]['properties']['FULLNAME'] = 'Matt Davis'
    assert features[1]['properties']['FULLNAME'] == 'TRAIL'
    assert out[1]['properties']['FULLNAME'] == 'Matt Davis'

    # geomType
    out = filterFeatures(features, geomType='Point')
    assert len(out)==1 and out[0]['geometry']['type']=='Point'

    # featureFunc
    def ffunc(feature,props): 
        if not props['OBJECTID'] > 1: return False
        props['FORMAL_NAME'] = 'Ms. ' + props['FULLNAME']
        return True

    out = filterFeatures(features, featureFunc=ffunc)
    assert len(out)==2
    assert out[0]['properties']['FORMAL_NAME'] == 'Ms. TRAIL'

    # colSpecs
    specs = [('num','INT','OBJECTID'),('name','INT','FORMAL_NAME')]
    out = filterFeatures(features, ffunc, geomType='LineString', colSpecs=specs)
    assert len(out) == 1
    assert out[0]['properties']['name'] == 'Ms. TRAIL'

    print 'geoutils test PASSED'

#doit
test()
