'''
Network base for Path Network
'''

import json
import os
import pdb
import tempfile

import geojson

import bins
import cannames
import geo 
import geofeatures
import log
import pnwk_namespace
import spatialref

class PNwkNetwork(pnwk_namespace.PNwkNamespace):
    FILE_EXTENSION = '.pnwk.geojson'

    def __init__(self,name=None, filename=None, units=None, quiet=False, srs=None):

        #spatial reference
        self.srs = srs

        #network name
        if not name:
            if filename: 
                name = filename
            else:
                name = 'nwk'

        # parent init (namespaces)
        super(PNwkNetwork,self).__init__(name=name)

        # scale constants in meters
        self.step_scale_m  = 0.3    # approximately one step
        self.street_scale_m = 8.0   # typical street width
        self.block_scale_m = 100.0   # typical distance between intersections

        # units
        if not units: units="meters"
        if units=="meters":
            self.units_per_meter = 1.0
        else: 
            if units =="feet":
                self.units_per_meter = 3.28084
            else:
                print "Unrecognized units:", units
                assert False
        f = self.units_per_meter
        self.stepScale = self.step_scale_m * f
        self.street_scale = self.street_scale_m * f
        self.block_scale = self.block_scale_m * f
        
        # segs and jcts
        self.segs = {}
        self.jcts = {}
        self.jct_bins = bins.Bins(self.block_scale)  # bins for searching for jcts by location
        self.last_gen_seg_id = 0
        self.last_gen_jct_id = 0

        if filename:
            self.read_geojson(filename, quiet=quiet)
      
    # qualifiedTags = tags with namespace prefixes.
    def add_seg(self, seg_id, from_jct_id, to_jct_id, points, names=(), tags=None, qualifiedTags=None):
        assert not self.segs.has_key(seg_id)
        #assert from_jct_id != to_jct_id  # looping segs happen e.g. "CARRINGTON LN" in Portland.
        assert len(points)>=2

        if not seg_id: seg_id = self._gen_seg_id()

        # make names canonical to facilitate comparison between networks from different sources
        cans = set([])
        for name in names: 
            canName = cannames.canonical_street_name(name)
            if len(canName)>0: cans.add(cannames.canonical_street_name(name))

        tags = self.add_namespace(tags,self.client_name_space)
        if qualifiedTags: tags.update(qualifiedTags)

        seg = self.Seg(
                network=self, 
                seg_id=seg_id, 
                points=points, 
                names=cans, 
                tags=tags)
                
        seg.from_jct = self._add_connection(from_jct_id, seg, start=True)
        seg.to_jct = self._add_connection(to_jct_id, seg, start=False)
        self.segs[seg_id] = seg

    # explicit add jct not necessary - useful mainly for adding tags.
    # multiple adds of same jct_id ok.  point needs to match, tags are updated on each call
    # qualifiedTags = tags with namespace prefixes.
    def add_jct(self, jct_id, point, tags=None, qualifiedTags=None):
        if not self.jcts.has_key(jct_id): self._add_jct(jct_id, point)
        jct = self.jcts[jct_id]
        assert jct.point == point

        tags = self.add_namespace(tags,self.client_name_space)
        if qualifiedTags: tags.update(qualifiedTags)
        jct.tags.update(tags)

    def split_seg(self, seg, d, fromBeginning, new_jct_id=None):
        if not new_jct_id: new_jct_id = self._gen_jct_id()
        assert new_jct_id < 0
        assert not self.jcts.has_key(new_jct_id)

        if fromBeginning:
            points, points2 = geo.cut(seg.points, d)
            jct2 = seg.to_jct

            seg.points = points
            seg.to_jct.segs.remove(seg)
            seg.to_jct = self._add_connection(new_jct_id, seg, start=False)
            
            self.add_seg(
                    seg_id=None, 
                    from_jct_id=new_jct_id, 
                    to_jct_id=jct2.jct_id, 
                    points=points2, 
                    names=list(seg.names), 
                    qualifiedTags=seg.tags
                    )
        else: 
            points2, points = geo.cut(seg.points, seg.length()-d)
            jct2 = seg.from_jct

            seg.points = points
            seg.from_jct.segs.remove(seg)
            seg.from_jct = self._add_connection(new_jct_id, seg, start=True)
            self.add_seg(
                    seg_id=None, 
                    from_jct_id=jct2.jct_id, 
                    to_jct_id=new_jct_id, 
                    points=points2, 
                    names=list(seg.names), 
                    qualifiedTags=seg.tags
                    )

    # create a new jct_id
    # (generated ids are negative)
    def _gen_jct_id(self):
        self.last_gen_jct_id -= 1
        new = self.last_gen_jct_id
        assert new not in self.jcts
        return new 
   
    # create a new seg_id
    # (generated ids are negative)
    def _gen_seg_id(self):
        self.last_gen_seg_id -= 1
        new = self.last_gen_seg_id
        assert new not in self.segs
        return new 

    def _add_jct(self, jct_id, point):
        assert not self.jcts.has_key(jct_id)
        jct = self.Jct(network=self, jct_id=jct_id, point=point)
        self.jcts[jct_id] = jct 
        self.jct_bins.add(point, jct)

    def _add_connection(self, jct_id, seg, start):
        assert type(seg) == self.Seg
        # junction coords
        if (start):
            point=seg.points[0]
        else:
            point=seg.points[-1]

        if not self.jcts.has_key(jct_id): self._add_jct(jct_id, point)
        jct = self.jcts[jct_id]
        assert jct.point == point
        jct.segs.add(seg)
        
        return jct

    @property
    def __geo_interface__(self):
        features = []
        for seg in self.segs.values(): features.append(seg.__geo_interface__)
        for jct in self.jcts.values(): features.append(jct.__geo_interface__)
        return geofeatures.geo_feature_collection(features, srs=self.srs)

    def _parse_geojson(self,geo):
        #print 'DEBUG _parse_geojson geo:', geo
        assert geo['type'] == 'FeatureCollection'

        # property namespace prefixes
        # TODO store pnwk name in json - for now name given at time of read MUST be the same.
        nsc = self.client_name_space
        nsp = self.pnwkNameSpace

        for feature in geo['features']:
            geometry = feature['geometry']
            properties = feature['properties']

            if geometry['type'] == 'Point':
                assert geometry['type'] == 'Point'
                jct_id = feature['id']
                point = tuple(geometry['coordinates'])

                # filter out pnwk properties
                tags={}
                for (key,value) in properties.items():
                    (ns, name) = self.split_off_namespace(key) 
                    if ns == nsp: continue
                    tags[key] = value
                #print 'tags',tags
                self.add_jct(jct_id, point, qualifiedTags=tags)

            else:
                assert geometry['type'] == 'LineString'
                seg_id = feature['id']
                points = [tuple(p) for p in geometry['coordinates']]
                from_jct_id = properties[nsp + 'from_jct_id']
                to_jct_id = properties[nsp + 'to_jct_id']
                points = [tuple(p) for p in geometry['coordinates']]
                try:
                    names = properties[nsp + 'name'].split(';')
                except KeyError:
                    names = ()

                # filter out pnwk properties
                tags={}
                for (key,value) in properties.items():
                    (ns, name) = self.split_off_namespace(key) 
                    if ns == nsp: continue
                    tags[key] = value

                self.add_seg(seg_id, from_jct_id, to_jct_id, points, names=names, qualifiedTags=tags)

    def read_geojson(self, filename, quiet=False): 
        if not quiet: log.info('Reading PNwk %s', filename)
        with open(filename+self.FILE_EXTENSION,'r') as f:
            # needs geojson>1.0.7, for non-ascii property keys
            geo = geojson.load(f)
        self._parse_geojson(geo)

    def write_geojson(self, name=None):
        if not name: name=self.name
        # using geo_interface for self is memory inefficient:  requires gen of geojson for entire pnwk
        #geofeatures.write_geojson(self, name+self.FILE_EXTENSION, srs=self.srs)
        geofeatures.write_geojson(
                self.segs.values()+self.jcts.values(), 
                name+self.FILE_EXTENSION, 
                srs=self.srs)

    def get_bbox(self):
        bbox = geo.BBox() 
        for jct in self.jcts.values():
            bbox.add_point(jct.point)
        return bbox.rect()

    def get_jcts_near_point(self, point, max_d=100):
        result = []
        for point,jct in self.jct_bins.in_radius(point,max_d):
            result.append(jct)
        return result

    def meters(self,length):
        return length / self.units_per_meter

    def feet(self,length):
        return self.meters(length) * 3.28084

    def miles(self,length):
        return self.meters(length) * 0.000621371

    def check_jcts(self):
        for jct_id,jct in self.jcts.items():
            assert jct.jct_id == jct_id
            assert jct.network == self
            jct.check()

    def check_segs(self):
        for seg_id,seg in self.segs.items():
            assert seg.seg_id == seg_id
            assert seg.network == self
            seg.check()

    def check(self):
        self.check_jcts()
        self.check_segs()

    class Seg(object):
        def __init__(self, network, seg_id, points, from_jct=None, to_jct=None, names=None, tags=None):
            self.names = set([]) 
            self.tags = {}
            self.match = None

            self.network = network
            self.seg_id = seg_id
            self.points = points
            self.from_bearing=geo.compass_bearing(points[0],points[1])
            self.to_bearing=geo.compass_bearing(points[-1],points[-2])
            self.from_jct = from_jct
            self.to_jct = to_jct
            if names: self.names.update(names)
            if tags: self.tags.update(tags)

        @property
        def __geo_interface__(self):
            geometry = geojson.LineString(self.points)
            return geojson.Feature(geometry=geometry, id=self.seg_id, properties=self._asdict())

        def _asdict(self):
            d = {}
            d.update(self.tags)
            ns = self.network.pnwkNameSpace

            if self.match: 
                d[ns + 'match_id'] = self.match.seg_id
                d[ns + 'match_rev'] = self.match_rev
            d[ns + 'seg_id'] = self.seg_id
            d[ns + 'length'] = self.length()
            d[ns + 'from_bearing'] = self.from_bearing
            d[ns + 'to_bearing'] = self.to_bearing
            d[ns + 'from_jct_id'] = self.from_jct.jct_id
            d[ns + 'to_jct_id'] = self.to_jct.jct_id
            if len(self.names) > 0: 
                d[ns + 'name'] = self.names_text()
            return d

        def names_text(self):
            return ';'.join(list(self.names))

        def other_end(self,jct):
            if self.from_jct == jct: 
                return self.to_jct
            else:
                assert self.to_jct == jct
                return self.from_jct

        def length(self, units=None):
            l = geo.length(self.points)
            if not units: return l
            if units == "feet":   return self.network.feet(l)
            if units == "meters": return self.network.meters(l)
            if units == "miles":  return self.network.miles(l)
            assert False

        def split(self, d, fromBeginning, new_jct_id=None):
            self.network.split_seg(self, d, fromBeginning, new_jct_id)
        
        def check(self):
            assert self.network.segs[self.seg_id] == self
            assert self.from_jct.network == self.network
            assert self.from_jct.point == self.points[0]
            assert self.to_jct.network == self.network
            assert self.to_jct.point == self.points[-1]

    class Jct(object):
        def __init__(self, network, jct_id, point):
            self.network = network
            self.jct_id = jct_id
            self.point = point
            self.segs = set([])
            self.tags = {}
            self.match = None

        @property
        def __geo_interface__(self):
            geometry = geojson.Point(self.point)
            return geojson.Feature(geometry=geometry, id=self.jct_id, properties=self._asdict())

        def _asdict(self):
            d = {}
            d.update(self.tags)
            ns = self.network.pnwkNameSpace
            d[ns + 'jct_id'] = self.jct_id
            d[ns + 'seg_ids'] = [seg.seg_id for seg in self.segs]
            if self.match: d['ns + match_id'] = self.match.jct_id
            if 'import_src' in d:
                d[ns + 'import_src_id'] = d['import_src'].jct_id
                del d['import_src']
            if 'export_count' in d:
                d[ns + 'export_count'] = d['export_count']
                del d['export_count']
            return d

        def names(self):
            nameSet = set([])
            for seg in self.segs:
                nameSet = nameSet.union(seg.names)
            return nameSet

        def check(self):
            for seg in self.segs: 
                assert self.network.jcts[self.jct_id] == self
                assert seg.network == self.network
                assert seg.from_jct == self or seg.to_jct == self
                assert not seg.match or (seg == seg.match.match)

def test_id_gen():
    pn = PNwkNetwork('pn')
    pn.check()
    assert pn._gen_jct_id() == -1
    assert pn._gen_jct_id() == -2
    assert pn._gen_seg_id() == -1
    assert pn._gen_seg_id() == -2

def test_setup_g(units=None):
    g = PNwkNetwork('g',units=units)    
    g.add_seg(1, 10, 11, test_points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])

    tags = { 'ele':1000, 'signage':'some', u'osm$stamv\xe4g': u'yes' }
    g.add_jct(10, g.segs[1].points[0], tags=tags)

    g.check()
    return g

def test_add_seg():
    g = test_setup_g()

    #print g.segs
    #print g.jcts
    assert len(g.segs) == 1
    assert len(g.jcts) == 2
    seg = g.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.from_jct.jct_id == 10
    assert seg.to_jct.jct_id == 11

def test_add_jct():
    g = test_setup_g()
    #print 'jcts[10].tags', g.jcts[10].tags
    assert g.jcts[10].tags['g$signage'] == 'some'
    assert g.jcts[10].tags['g$ele'] == 1000

def test_geo_interface():
    g = test_setup_g()
    seg = g.segs[1]
    geo = seg.__geo_interface__
    #print 'geo:', geo
    assert geo['geometry']['type'] == 'LineString'
    assert geo['geometry']['coordinates'][1] == seg.points[1]
    assert geo['properties']['g_pnwk$from_jct_id'] == 10

def _test_read_write1(fname,fname2):
    g = test_setup_g()
    seg = g.segs[1]
     
    g.write_geojson(fname)
    g2 = PNwkNetwork(name='g', filename=fname, quiet=True)
    assert len(g2.segs) == 1
    assert len(g2.jcts) == 2
    seg = g2.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.from_jct.jct_id == 10
    assert seg.to_jct.jct_id == 11
    assert g2.jcts[10].tags['g$signage'] == 'some'
    assert g2.jcts[10].tags['g$ele'] == 1000
    g2.check()
    
    g2.write_geojson(fname2)
    g3 = PNwkNetwork(name='g', filename=fname2, quiet=True)
    assert len(g3.segs) == 1
    assert len(g3.jcts) == 2
    seg = g3.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.from_jct.jct_id == 10
    assert seg.to_jct.jct_id == 11
    assert g2.jcts[10].tags['g$signage'] == 'some'
    assert g2.jcts[10].tags['g$ele'] == 1000
    g3.check()

def test_read_write():
    tmp_dir = tempfile.gettempdir()
    fname = os.path.join(tmp_dir,'spiderosm_pnwk_network_test')
    fname2 = fname +'2'
    try:
        _test_read_write1(fname=fname,fname2=fname2)
    finally:
        if os.path.exists(fname): os.remove(fname)
        if os.path.exists(fname2): os.remove(fname2)

def test_get_jcts_near_point():
    g = test_setup_g()
    nj = g.get_jcts_near_point((0,0), max_d=1500)
    nj2 = g.get_jcts_near_point((0,0))
    #print nj
    #print 'nj2:',nj2
    assert len(nj) == 2
    assert len(nj2) == 1
    g.check()

def test_get_bbox():
    g = test_setup_g()
    box = g.get_bbox()
    #print 'box:',box
    assert box == (0,0,1000,1000)
    g.check()

def test_units():
    gft = test_setup_g(units="feet")
    gm = test_setup_g(units="meters")
    segft = gft.segs[1]
    segm = gm.segs[1]
    assert round(segft.length())== 1414 and round(segft.length(units="meters"))==431
    assert round(segm.length(units="feet"))==4640 and round(segm.length("miles")*100)==88

test_points = [(0,0), (1000,1000)]
test_points2 = [(5,0), (1005,1000)]
def test():
    test_units()
    test_id_gen()
    test_add_seg()
    test_add_jct()
    test_geo_interface()
    test_read_write()
    test_get_jcts_near_point()
    test_get_bbox()

    print 'pnwk_network PASS'

#doit
if __name__ == "__main__":
    test()
    #_test_read_write1(fname='foo1',fname2='foo2')
 
