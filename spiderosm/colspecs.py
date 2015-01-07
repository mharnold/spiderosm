#TODO clean this up with ColSpecs class
import numbers

import geojson

import geo
import geofeatures

# auto gen colspecs from geo features
def gen(geo, geometry_type=None):
    features=geofeatures.geo_features(geo)
    geo_type_table = {'LineString':'LINESTRING', 'Point':'POINT'}
    type_name = { numbers.Integral:'INT', numbers.Real:'FLOAT', basestring:'TEXT'}
    type_rank = { numbers.Integral:1, numbers.Real:2, basestring:3 }

    def make_bigint_specs(specs, features, geometry_type):
        for (prop,type_name) in specs.items():
            if type_name != 'INT': continue
            for feature in features:
                if feature['geometry']['type'] != geometry_type: continue
                if abs(feature['properties'].get(prop,0)) > 2**30: 
                    specs[prop] = 'BIGINT'
                    break

    if not geometry_type: geometry_type = features[0]['geometry']['type']
    specs = {}
    specs_rank = {}

    # auto create 'col types' based on python types of values
    # if attribute values not of same type, promote based on type_rank
    for feature in features:
        if feature['geometry']['type'] != geometry_type: continue
        for (prop,value) in feature['properties'].items():
            if value==None: continue
            if isinstance(value,numbers.Integral):      # includes int and long
                t = numbers.Integral
            elif isinstance(value,numbers.Real): 
                t = numbers.Real
            elif isinstance(value,basestring):  # includes unicode
                t = basestring
            else:
                t = basestring # anything weird goes to TEXT.
            if specs_rank.get(prop,0) >= type_rank[t]: continue        
            specs[prop] = type_name[t]
            specs_rank[prop] = type_rank[t]

    # promote 'INT' attributes with large values to 'BIGINT'
    make_bigint_specs(specs, features, geometry_type)
    col_specs = sorted(specs.items())
    
    # add geometry as last column
    col_specs.append(('geometry', geo_type_table[geometry_type]))
    
    return col_specs

# uniquifies col names to avoid collisions due to case-insenstivity, and fills out prop_names
def fix(col_specs):
    def suffix (i): 
        if i==0: return ''
        return '$%d' % i
    lc_names = {}
    new_col_specs = []
    for col_spec in col_specs:
        col_name = col_spec[0]
        if len(col_spec) >= 2:
            col_type = col_spec[1]
        else:
            col_type = 'TEXT'
        if len(col_spec) >=3:
            prop_name = cols_spec[2]
        else:
            prop_name = col_name

        i=0
        while col_name.lower() + suffix(i) in lc_names: i += 1
        lc_names[col_name.lower() + suffix(i)] = True 
        new_col_specs.append((col_name + suffix(i), col_type, prop_name))
        
    return new_col_specs

def _make_geo():
    geometry = geojson.Point((-122.0,38.0))
    ls = geojson.LineString([(-122,38),(-122,39)])
    features = [
        geojson.Feature(geometry=geometry, id=1, properties={'name':'john','addr':1212, 'gpa':3.5}),
        geojson.Feature(geometry=geometry, id=2, properties={'fish':'salmon', 'addr':'sea', 'gpa':3, 'foo':None}),
        geojson.Feature(geometry=ls, id=10, properties={'other':10}),
        geojson.Feature(geometry=geometry, id=3, properties={'num':2**80}),
        geojson.Feature(geometry=geometry, id=4, properties={'Num':2}),
        geojson.Feature(geometry=geometry, id=5, properties={'NUM':'many'})
        ]
    geo = geojson.FeatureCollection(features)
    return geo

def test():
    geo = _make_geo()
    col_specs = gen(geo)
    col_specs = fix(col_specs)
    assert col_specs == [('NUM', 'TEXT', 'NUM'), ('Num$1', 'INT', 'Num'), 
            ('addr', 'TEXT', 'addr'), ('fish', 'TEXT', 'fish'), ('gpa', 'FLOAT', 'gpa'), 
            ('name', 'TEXT', 'name'), ('num$2', 'BIGINT', 'num'), ('geometry', 'POINT', 'geometry')]

    col_specs = gen(geo,geometry_type='LineString')
    #print 'col_specs',col_specs
    assert col_specs == [('other','INT'), ('geometry','LINESTRING')]

    print "colspecs PASS"

#doit
if __name__ == "__main__":
    test()

