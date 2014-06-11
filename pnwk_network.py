'''
Network base for Path Network
'''
import pdb

import geojson

import bins
import geo 
import names as canNames
import pnwk_namespace

class PNwkNetwork(pnwk_namespace.PNwkNamespace):
    fileExtension = '.pnwk.geojson'

    def __init__(self,name=None,filename=None, units=None):

        #network name
        if not name:
            if filename: 
                name = filename
            else:
                name = 'nwk'

        # parent init (namespaces)
        super(PNwkNetwork,self).__init__(name=name)

        # scale constants in meters
        self.stepScaleM  = 0.3    # approximately one step
        self.streetScaleM = 8.0   # typical street width
        self.blockScaleM = 100.0   # typical distance between intersections

        # units
        if not units: units="meters"
        if units=="meters":
            self.unitsPerMeter = 1.0
        else: 
            if units =="feet":
                self.unitsPerMeter = 3.28084
            else:
                print "Unrecognized units:", units
                assert False
        f = self.unitsPerMeter
        self.stepScale = self.stepScaleM * f
        self.streetScale = self.streetScaleM * f
        self.blockScale = self.blockScaleM * f
        
        # segs and jcts
        self.segs = {}
        self.jcts = {}
        self.jctBins = bins.Bins(self.blockScale)  # bins for searching for jcts by location
        self.lastGenSegId = 0
        self.lastGenJctId = 0

        if filename:
            self.readGeojson(filename)
      
    # qualifiedTags = tags with namespace prefixes.
    def addSeg(self, segId, fromJctId, toJctId, points, names=(), tags=None, qualifiedTags=None):
        assert not self.segs.has_key(segId)
        #assert fromJctId != toJctId  # looping segs happen e.g. "CARRINGTON LN" in Portland.
        assert len(points)>=2

        if not segId: segId = self.genSegId()

        # make names canonical to facilitate comparison between networks from different sources
        cans = set([])
        for name in names: 
            canName = canNames.canonical_street_name(name)
            if len(canName)>0: cans.add(canNames.canonical_street_name(name))

        tags = self.addNamespace(tags,self.clientNameSpace)
        if qualifiedTags: tags.update(qualifiedTags)

        seg = self.Seg(
                network=self, 
                segId=segId, 
                points=points, 
                names=cans, 
                tags=tags)
                
        seg.fromJct = self._addConnection(fromJctId, seg, start=True)
        seg.toJct = self._addConnection(toJctId, seg, start=False)
        self.segs[segId] = seg

    def splitSeg(self, seg, d, fromBeginning, newJctId=None):
        if not newJctId: newJctId = self.genJctId()
        assert newJctId < 0
        assert not self.jcts.has_key(newJctId)

        if fromBeginning:
            points, points2 = geo.cut(seg.points, d)
            jct2 = seg.toJct

            seg.points = points
            seg.toJct.segs.remove(seg)
            seg.toJct = self._addConnection(newJctId, seg, start=False)
            
            self.addSeg(
                    segId=None, 
                    fromJctId=newJctId, 
                    toJctId=jct2.jctId, 
                    points=points2, 
                    names=list(seg.names), 
                    qualifiedTags=seg.tags
                    )
        else: 
            points2, points = geo.cut(seg.points, seg.length()-d)
            jct2 = seg.fromJct

            seg.points = points
            seg.fromJct.segs.remove(seg)
            seg.fromJct = self._addConnection(newJctId, seg, start=True)
            self.addSeg(
                    segId=None, 
                    fromJctId=jct2.jctId, 
                    toJctId=newJctId, 
                    points=points2, 
                    names=list(seg.names), 
                    qualifiedTags=seg.tags
                    )

    # create a new jctId
    # (generated ids are negative)
    def genJctId(self):
        self.lastGenJctId -= 1
        new = self.lastGenJctId
        assert new not in self.jcts
        return new 
   
    # create a new segId
    # (generated ids are negative)
    def genSegId(self):
        self.lastGenSegId -= 1
        new = self.lastGenSegId
        assert new not in self.segs
        return new 

    def _add_jct(self, jctId, point):
        assert not self.jcts.has_key(jctId)
        jct = self.Jct(network=self, jctId=jctId, point=point)
        self.jcts[jctId] = jct 
        self.jctBins.add(point, jct)

    def _addConnection(self, jctId, seg, start):
        assert type(seg) == self.Seg
        # junction coords
        if (start):
            point=seg.points[0]
        else:
            point=seg.points[-1]

        if not self.jcts.has_key(jctId): self._add_jct(jctId, point)
        jct = self.jcts[jctId]
        assert jct.point == point
        jct.segs.add(seg)
        
        return jct

    @property
    def __geo_interface__(self):
        features = []
        for seg in self.segs.values(): features.append(seg.__geo_interface__)
        for jct in self.jcts.values(): features.append(jct.__geo_interface__)
        return geojson.FeatureCollection(features)

    def _parseGeojson(self,geo):
        #print 'DEBUG _parseGeojson geo:', geo
        assert geo['type'] == 'FeatureCollection'

        # property namespace prefixes
        # TODO store pnwk name in json - for now name given at time of read MUST be the same.
        nsc = self.clientNameSpace
        nsp = self.pnwkNameSpace

        for feature in geo['features']:
            geometry = feature['geometry']
            properties = feature['properties']

            if geometry['type'] != 'LineString':
                # not reading jcts yet.
                continue
            segId = feature['id']
            points = [tuple(p) for p in geometry['coordinates']]
            fromJctId = properties[nsp + 'fromJctId']
            toJctId = properties[nsp + 'toJctId']
            points = [tuple(p) for p in geometry['coordinates']]
            try:
                names = properties[nsp + 'name'].split(';')
            except KeyError:
                names = ()

            # filter out pnwk properties
            tags={}
            for (key,value) in properties.items():
                (ns, name) = self.splitOffNamespace(key) 
                if ns == nsp: continue
                tags[key] = value

            self.addSeg(segId, fromJctId, toJctId, points, names=names, qualifiedTags=tags)

    def readGeojson(self,filename): 
        print 'DEBUG readGeojson filename:', filename
        f = open(filename+self.fileExtension,'r')
        geo = geojson.load(f)
        f.close()
        self._parseGeojson(geo)

    def writeGeojson(self, name=None):
        if not name: name=self.name
        f = open(name+self.fileExtension,'w')
        geojson.dump(self.__geo_interface__,f,indent=2,sort_keys=True)
        f.close()

    def getBBox(self):
        bbox = geo.BBox() 
        for jct in self.jcts.values():
            bbox.add_point(jct.point)
        return bbox.rect()

    def getJctsNearPoint(self, point, maxd=100):
        result = []
        for point,jct in self.jctBins.inRadius(point,maxd):
            result.append(jct)
        return result

    def meters(self,length):
        return length / self.unitsPerMeter

    def feet(self,length):
        return self.meters(length) * 3.28084

    def miles(self,length):
        return self.meters(length) * 0.000621371

    def check_jcts(self):
        for jctId,jct in self.jcts.items():
            assert jct.jctId == jctId
            assert jct.network == self
            jct.check()

    def check_segs(self):
        for segId,seg in self.segs.items():
            assert seg.segId == segId
            assert seg.network == self
            seg.check()

    def check(self):
        self.check_jcts()
        self.check_segs()

    class Seg(object):
        def __init__(self, network, segId, points, fromJct=None, toJct=None, names=None, tags=None):
            self.names = set([]) 
            self.tags = {}
            self.match = None

            self.network = network
            self.segId = segId
            self.points = points
            self.fromBearing=geo.compass_bearing(points[0],points[1])
            self.toBearing=geo.compass_bearing(points[-1],points[-2])
            self.fromJct = fromJct
            self.toJct = toJct
            if names: self.names.update(names)
            if tags: self.tags.update(tags)

        @property
        def __geo_interface__(self):
            geometry = geojson.LineString(self.points)
            return geojson.Feature(geometry=geometry, id=self.segId, properties=self._asdict())

        def _asdict(self):
            d = {}
            d.update(self.tags)
            ns = self.network.pnwkNameSpace

            if self.match: 
                d[ns + 'matchId'] = self.match.segId
                d[ns + 'matchRev'] = self.matchRev
            d[ns + 'segId'] = self.segId
            d[ns + 'length'] = self.length()
            d[ns + 'fromBearing'] = self.fromBearing
            d[ns + 'toBearing'] = self.toBearing
            d[ns + 'fromJctId'] = self.fromJct.jctId
            d[ns + 'toJctId'] = self.toJct.jctId
            if len(self.names) > 0: 
                d[ns + 'name'] = self.namesText()
            return d

        def namesText(self):
            return ';'.join(list(self.names))

        def otherEnd(self,jct):
            if self.fromJct == jct: 
                return self.toJct
            else:
                assert self.toJct == jct
                return self.fromJct

        def length(self, units=None):
            l = geo.length(self.points)
            if not units: return l
            if units == "feet":   return self.network.feet(l)
            if units == "meters": return self.network.meters(l)
            if units == "miles":  return self.network.miles(l)
            assert False

        def split(self, d, fromBeginning, newJctId=None):
            self.network.splitSeg(self, d, fromBeginning, newJctId)
        
        def check(self):
            assert self.network.segs[self.segId] == self
            assert self.fromJct.network == self.network
            assert self.fromJct.point == self.points[0]
            assert self.toJct.network == self.network
            assert self.toJct.point == self.points[-1]

    class Jct(object):
        def __init__(self, network, jctId, point):
            self.network = network
            self.jctId = jctId
            self.point = point
            self.segs = set([])
            self.tags = {}
            self.match = None

        @property
        def __geo_interface__(self):
            geometry = geojson.Point(self.point)
            return geojson.Feature(geometry=geometry, id=self.jctId, properties=self._asdict())

        def _asdict(self):
            d = {}
            d.update(self.tags)
            ns = self.network.pnwkNameSpace
            d[ns + 'jctId'] = self.jctId
            d[ns + 'segIds'] = [seg.segId for seg in self.segs]
            if self.match: d['ns + matchId'] = self.match.jctId
            if 'importSrc' in d:
                d[ns + 'importSrcId'] = d['importSrc'].jctId
                del d['importSrc']
            return d

        def names(self):
            nameSet = set([])
            for seg in self.segs:
                nameSet = nameSet.union(seg.names)
            return nameSet

        def check(self):
            for seg in self.segs: 
                assert self.network.jcts[self.jctId] == self
                assert seg.network == self.network
                assert seg.fromJct == self or seg.toJct == self
                assert not seg.match or (seg == seg.match.match)

def testIdGen():
    pn = PNwkNetwork('pn')
    pn.check()
    assert pn.genJctId() == -1
    assert pn.genJctId() == -2
    assert pn.genSegId() == -1
    assert pn.genSegId() == -2

def testSetupG(units=None):
    g = PNwkNetwork('g',units=units)    
    g.addSeg(1, 10, 11, test_points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])
    g.check()
    return g

def testAddSeg():
    g = testSetupG()

    #print g.segs
    #print g.jcts
    assert len(g.segs) == 1
    assert len(g.jcts) == 2
    seg = g.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.fromJct.jctId == 10
    assert seg.toJct.jctId == 11

def testGeoInterface():
    g = testSetupG()
    seg = g.segs[1]
    geo = seg.__geo_interface__
    #print 'geo:', geo
    assert geo['geometry']['type'] == 'LineString'
    assert geo['geometry']['coordinates'][1] == seg.points[1]
    assert geo['properties']['g_pnwk$fromJctId'] == 10

def testReadWrite():
    fname = 'spiderosm_pnwk_network_test'
    fname2 = fname +'2'
    g = testSetupG()
    seg = g.segs[1]
     
    g.writeGeojson(fname)
    g2 = PNwkNetwork(name='g',filename=fname)
    assert len(g2.segs) == 1
    assert len(g2.jcts) == 2
    seg = g2.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.fromJct.jctId == 10
    assert seg.toJct.jctId == 11
    g2.check()
    
    g2.writeGeojson(fname2)
    g3 = PNwkNetwork(name='g',filename=fname2)
    assert len(g3.segs) == 1
    assert len(g3.jcts) == 2
    seg = g3.segs[1]
    assert len(seg.names) == 2
    assert seg.points[1] == test_points[1]
    assert seg.fromJct.jctId == 10
    assert seg.toJct.jctId == 11
    g3.check()

def testGetJctsNearPoint():
    g = testSetupG()
    nj = g.getJctsNearPoint((0,0), maxd=1500)
    nj2 = g.getJctsNearPoint((0,0))
    #print nj
    #print 'nj2:',nj2
    assert len(nj) == 2
    assert len(nj2) == 1
    g.check()

def testGetBBox():
    g = testSetupG()
    box = g.getBBox()
    #print 'box:',box
    assert box == (0,0,1000,1000)
    g.check()

def testUnits():
    gft = testSetupG(units="feet")
    gm = testSetupG(units="meters")
    segft = gft.segs[1]
    segm = gm.segs[1]
    assert round(segft.length())== 1414 and round(segft.length(units="meters"))==431
    assert round(segm.length(units="feet"))==4640 and round(segm.length("miles")*100)==88

test_points = [(0,0), (1000,1000)]
test_points2 = [(5,0), (1005,1000)]
def test():
    testUnits()
    testIdGen()
    testAddSeg()
    testGeoInterface()
    testReadWrite()
    testGetJctsNearPoint()
    testGetBBox()

    print 'pnwk_network test PASSED'

#doit
test()
 
