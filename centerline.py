'''
Street Centerline Data to Path Network conversion
'''
import pdb

import pnwk

''' features in python geo interface format (geojson) '''
def make_pnwk(features, props=None, namesFunc=None, filter_func=None, name=None):
    print 'num centerline features:', len(features)
    #print 'DEBUG random city feature:',features[10]

    city_street_network = pnwk.PNwk(name=name)
    num_segs = 0
    num_jcts=[0]  # this is a hack to get around scoping issues
    jct_ids = {}  # indexed by jct coords
    skipped_features = []

    # return jct_id for point (assigning new one if needed)
    def jct_id(point):
        if jct_ids.has_key(point):
            return jct_ids[point]
        else:
            num_jcts[0] += 1 
            jct_ids[point] = num_jcts[0]
            return num_jcts[0]

    for feature in features:
        if filter_func and not filter_func(feature): continue

        geometry = feature['geometry']
        if geometry['type'] == 'MultiLineString':
            parts = geometry['coordinates']
        else:
            if geometry['type'] == 'LineString':
                parts = [geometry['coordinates']]
            else:
                parts = []
                skippedFeatures.append(feature)

        for part in parts:
            num_segs += 1
            seg_id = num_segs
            points = [tuple(l) for l in part]
            start_point = points[0];
            end_point = points[-1]

            if not props:
                tags = feature['properties']
            else:
                tags = {}
                for prop in props:
                    if prop in feature['properties']: 
                        tags[prop] = feature['properties'][prop]

            city_street_network.add_seg(seg_id, jct_id(start_point), jct_id(end_point), points,
                    names=namesFunc(feature),
                    tags=tags
                    )
   
    if len(skipped_features) > 0:
        print '%d features skipped.' % len(skipped_features)
        print 'first skipped feature:',feature

    return city_street_network

def rlis_pnwk(features,name=None,props=None):
    def rlis_names(feature):
        def _rlis_names0(prefix,streetname,ftype):
            #print 'DEBUG _rlis_names0 prefix,streetname,ftype', prefix,streetname,ftype

            if not streetname or streetname=='UNNAMED': return []
            names = []

            # <prefix> <streetname> <ftype>
            name = ''
            if prefix: name += (prefix + ' ')
            name += streetname
            if ftype: name += (' ' + ftype)
            names.append(name)

            # split out names in RAMPs
            if ftype == 'RAMP':
                for sname in streetname.split('-'):
                    names += _rlis_names0(prefix,sname,'')
                    names += _rlis_names0('',sname,'')  # want 'I205' not 'NE I205'
            
            #print 'DEBUG _rlis_names0 names', names 
            return names
        properties = feature['properties']
        prefix = properties.get('PREFIX')
        streetname = properties.get('STREETNAME')
        ftype = properties.get('FTYPE')
        return _rlis_names0(prefix,streetname,ftype)
    #return make_pnwk(features,'LOCALID',namesFunc=rlis_names,name=name)
    return make_pnwk(features,props=props,namesFunc=rlis_names,name=name)

def berkeley_pnwk(features,name=None,props=None):
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

    return make_pnwk(features,props=props,namesFunc=berkeley_names,filter_func=berkeley_filter,name=name)

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
        "FULLNAME": "I80 E UNIVERSITY RAMP", 
        "CATEGORY": "CONNECTOR"
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
        "type": "LineString", 
        "coordinates": [ [100,110],[200,210] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 10, 
        "FULLNAME": "filter me",
        "CATEGORY": "LIGHT RAIL"
      }
    }]

    pnwk = berkeley_pnwk(features)
    assert len(pnwk.segs) == 2
    names = pnwk.segs[1].names
    assert len(names) == 2
    assert 'I 80 E UNIVERSITY RAMP' in names
    assert 'I 80' in names
    assert len(pnwk.segs[2].names_text()) == 0

    print 'centerline test PASSED'

#doit 
test()
