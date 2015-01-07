'''
Street Centerline Data to Path Network conversion
'''
import pdb

import geo
import log
import pnwk

''' features in python geo interface format (geojson) '''
def make_pnwk(features, props=None, namesFunc=None, filter_func=None, name=None,quiet=False, clip_rect=None):
    if not quiet: log.info('%d centerline features.', len(features))
    #print 'DEBUG random city feature:',features[10]

    city_street_network = pnwk.PNwk(name=name)
    num_segs = 0
    num_jcts=[0]  # this is a hack to get around scoping issues
    jct_ids = {}  # indexed by jct coords
    skipped_features = []
    max_input_dim = 0

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
            points = []
            for l in part:
                #code assumes 2d coords, retaining only first 2 coords of input.
                points.append(tuple(l[:2]))
                max_input_dim = max(max_input_dim,len(l))
            start_point = points[0];
            end_point = points[-1]

            if not props:
                tags = feature['properties']
            else:
                tags = {}
                for prop in props:
                    if prop in feature['properties']: 
                        tags[prop] = feature['properties'][prop]

            if clip_rect and not geo.points_intersect_rect_q(points, clip_rect): continue 

            city_street_network.add_seg(seg_id, jct_id(start_point), jct_id(end_point), points,
                    names=namesFunc(feature),
                    tags=tags
                    )
   
    if len(skipped_features) > 0  and not quiet:
        log.warning('%d features skipped.\n'
                '  first skipped feature: %s',
                len(skipped_features), 
                str(feature))

    if max_input_dim > 2 and not quiet:
        info.warning('Input coordinates up to %d dimensional.\n' 
                '  Retaining only first 2 dimensions.',
                max_input_dim)

    return city_street_network


# EXAMPLE APPLICATIONS OF centerline.make_pnwk
# (See also example toplevels e.g. spiderosm/bin/spiderosm_berkeley.py)

# RLIS centerline data -> pnwk
def rlis_pnwk(features,name=None,props=None,quiet=False,clip_rect=None):
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
    return make_pnwk(features,
            props=props,
            namesFunc=rlis_names,
            name=name,
            quiet=quiet,
            clip_rect=clip_rect)

#Berkeley centerline data -> pnwk
def berkeley_pnwk(features, name=None, props=None, quiet=False, clip_rect=None):
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

    return make_pnwk(features,
            props=props,
            namesFunc=berkeley_names,
            filter_func=berkeley_filter,
            name=name,
            quiet=quiet,
            clip_rect=clip_rect)

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
        "coordinates": [ [100,110, 100],[200,210, 110] ]
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
        "coordinates": [ [100,110, 100],[200,210] ]
        }, 
      "type": "Feature", 
      "properties": {
        "OBJECTID": 10, 
        "FULLNAME": "filter me",
        "CATEGORY": "LIGHT RAIL"
      }
    }]

    pnwk = berkeley_pnwk(features,quiet=True)
    assert len(pnwk.segs) == 2
    names = pnwk.segs[1].names
    assert len(names) == 2
    assert 'I 80 E UNIVERSITY RAMP' in names
    assert 'I 80' in names
    assert len(pnwk.segs[2].names_text()) == 0

    # test clipping
    clip_rect = [ 15,15,25,25 ] 
    pnwk = berkeley_pnwk(features,quiet=True,clip_rect=clip_rect)
    assert len(pnwk.segs) == 1
    assert 'I 80 E UNIVERSITY RAMP' in pnwk.segs[1].names

    print 'centerline PASS'

#doit 
if __name__ == "__main__":
    test()
