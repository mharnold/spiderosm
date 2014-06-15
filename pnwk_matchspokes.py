'''
Path Network - Match 'spokes,' crawling outward from already matched jcts, and splitting longer segments as needed.
'''
import pdb

import geo 
import pnwk_matchjcts

class PNwkMatchSpokes(pnwk_matchjcts.PNwkMatchJcts):
    class Jct(pnwk_matchjcts.PNwkMatchJcts.Jct):
        def spokes(self):
            spokes=[]
            for seg in self.segs:
                spokes.append(Spoke(jct=self, seg=seg))
            return spokes

    # match nwk2 into nwk1
    # matches are searched for in radius d and must be unique within that radius in both networks
    def spokeCrawl(self, startJctMatchList, msg=None, quiet=False):
        if msg: print 'SPOKECRAWL:',msg
        newJctMatches = startJctMatchList
        passNum = 0
        while len(newJctMatches)>0:
            passNum += 1
            print 'pass %d, processing %d matched junctions:' % (passNum, len(newJctMatches))
            newJctMatches = matchSpokes(newJctMatches)

        return passNum>1

class Spoke(object):
    def __init__(self, jct, seg):
        assert jct.network == seg.network
        self.jct = jct
        self.seg = seg

        if seg.fromJct == jct:
            self.bearing = seg.fromBearing
        else:
            assert seg.toJct == jct
            self.bearing = seg.toBearing

    # is spoke direction reversed from segment direction
    def upstream(self):
        return self.seg.toJct == self.jct

    # return jct at far end of spoke
    def end(self):
        return self.seg.otherEnd(self.jct)

    # return spoke that continues on from far end of this spoke (if any)
    def next(self):
        jct = self.end()
        bestDelta = 180
        bestSpoke = None;
        for spoke in jct.spokes():
            delta = geo.compass_bearing_delta(self.bearing,spoke.bearing)
            if delta<bestDelta: 
                bestSpoke = spoke
                bestDelta = delta
        if bestDelta > 90: return None
        return bestSpoke

    # return point at distance d along spoke
    def interpolate(self,d):
        if self.upstream(): 
            deff = self.length() - d
        else:
            deff = d

        assert -0.000001 <= d and d <= self.length() + .000001
        return geo.interpolate(self.seg.points,deff)

     # return distance along spoke to nearest approach to point
    def project(self,point):
        d = geo.project(self.seg.points,point)
        if self.upstream(): d = self.length() - d
        return d

    def length(self):
        return self.seg.length()

    # trim spoke length (by splitting seg)
    def trim(self,d,newJctId=None):
        assert 0<d and d<self.length()
        fromBeginning = not self.upstream()
        self.seg.split(d, fromBeginning, newJctId=newJctId) 
        assert not newJctId or self.end().jctId==newJctId

    # return subset of spokes that match self (along with distances along spokes of match)
    def match(self, spokes):
        matchSet = []
        if self.seg.match: return matchSet

        len1 = self.length()
        streetScale = self.seg.network.streetScale
        for spoke in spokes:
            if spoke.seg.match: continue
            len2 = spoke.length()

            if len1<=len2:
                length = len1
                d1=length
                d2=spoke.project(self.end().point)
            else:
                length = len2
                d1 = self.project(spoke.end().point)
                d2 = length

            # to match, segments must be approximately same length
            if abs(d1-d2) > max(streetScale, 0.1*length): continue

            # to match, segment end points must be near each other
            if geo.distance(self.interpolate(d1),spoke.interpolate(d2)) > streetScale: continue

            matchSet.append((self, d1, spoke, d2))

        return matchSet
 
def trimSpokeQ(shorter, longer, d):

    # if length difference significant, trim
    if abs(longer.length()-d)>longer.seg.network.streetScale:
        return True 
   
    # if next point after shorter spoke end is better match for longer end, trim!
    nextShorter = shorter.next()
    if nextShorter:
        delta_next = geo.distance(longer.end().point, nextShorter.end().point)
        delta_this = geo.distance(longer.end().point, shorter.end().point)
        return delta_next < delta_this

    # no good reason to trim
    return False
      
# consider trimming longer spoke.
def trimMatchedSpokes(spoke1, d1, spoke2, d2):
    length1 = spoke1.length()
    length2 = spoke2.length()

    # make spoke1 the short one.
    if(length1>length2):
        trimMatchedSpokes(spoke2, d2, spoke1, d1)
        return
    assert length1<=length2
    assert length1==d1

    shorter = spoke1
    longer = spoke2
    d = d2

    # stay away from ends
    middle = length2/2.0
    if d<1: d= min(1,middle)
    if length2-d<1: d = max(middle,length2-1)

    long = spoke2
    if trimSpokeQ(shorter, longer, d):
        longer.trim(d)
        shorter.end().tags['exportCount'] = shorter.end().tags.get('exportCount',0) + 1
        longer.end().tags['importSrc'] = shorter.end()

def matchJctSpokes(jct1, jct2):
    global there
    assert jct1.network != jct2.network
    newJctMatches = []
    
    spokes1 = jct1.spokes()
    spokes2 = jct2.spokes()
    #print 'len1, len2:', len(spokes1), len(spokes2)

    for spoke1 in spokes1:
        matchSet = spoke1.match(spokes2)
        
        #matches must be unique
        if len(matchSet) != 1: continue

        spoke1x,d1,spoke2,d2 = matchSet[0]
        assert spoke1x == spoke1

        #matches must be unique in both directions
        matchSet2 = spoke2.match(spokes1)
        assert spoke1 in [ m[2] for m in matchSet2 ]
        if len(matchSet2) != 1: continue

        assert not spoke1.seg.match
        assert not spoke2.seg.match

        # consider trimming longer spoke
        trimMatchedSpokes(spoke1, d1, spoke2, d2)

        # match spoke segs
        #jct1.network.check() #DEBUG!
        #jct2.network.check()
        assert not spoke1.seg.match
        assert not spoke2.seg.match
        spoke1.seg.match = spoke2.seg
        spoke2.seg.match = spoke1.seg
        #jct1.network.check()
        #jct2.network.check()

        # sense of matched segs same or reverse?
        if spoke1.upstream() == spoke2.upstream():
            rev = 0
        else:
            rev = 1
        spoke1.seg.matchRev = rev
        spoke2.seg.matchRev = rev

        # continue spoke crawl where we left off.
        newJctMatches.append((spoke1.end(), spoke2.end()))
        there = False

    return newJctMatches

def matchSpokes(jctMatchList):
    newJctMatches = []
    for (jct1,jct2) in jctMatchList:
        newJctMatches += matchJctSpokes(jct1, jct2)
    return newJctMatches


def test():
    points = [(0,0), (1000,1000)]
    points2 = [(5,0), (1005,1000)]
    g = PNwkMatchSpokes('g')    
    g.addSeg(1, 10, 11, points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])

    # test spokes
    spokes = g.jcts[10].spokes()
    assert len(spokes)==1 and spokes[0].bearing==45 and spokes[0].seg.segId==1 
    spokes = g.jcts[11].spokes()
    assert len(spokes)==1 and spokes[0].bearing==225 and spokes[0].seg.segId==1 
    g.check()

    # test segment and spoke length
    n3 = PNwkMatchSpokes('n3_nwk')
    points3 = [(0,0),(1,0),(1,1)]
    n3.addSeg(1, 10, 11, points3)
    assert n3.segs[1].length() == 2
    assert n3.jcts[11].spokes()[0].length() == 2

    # test spoke.end()
    assert n3.jcts[10].spokes()[0].end() == n3.jcts[11]
    assert n3.jcts[11].spokes()[0].end() == n3.jcts[10]

    # test spoke.upstream()
    spoke_out = n3.jcts[10].spokes()[0]
    spoke_in = n3.jcts[11].spokes()[0]
    assert not spoke_out.upstream()
    assert spoke_in.upstream()

    # test spoke.interpolate()
    assert spoke_out.interpolate(0) == (0,0)
    assert spoke_out.interpolate(1.5) == (1,0.5)
    assert spoke_in.interpolate(0) == (1,1)
    assert spoke_in.interpolate(1.5) == (0.5,0)

    # test spoke.project()
    assert spoke_out.project((10,0.5)) == 1.5
    assert spoke_in.project((10,0.5)) == 0.5

    # test spoke.trim()
    spoke_in.trim(0.5,-1)
    spoke_out = n3.jcts[10].spokes()[0]
    spoke_out.trim(0.5,-2)
    assert len(n3.jcts) == 4
    assert len(n3.segs) == 3
    assert spoke_in.end().point == (1,0.5)
    assert spoke_out.end().point == (0.5,0)

    # test spoke.next()
    nstar = PNwkMatchSpokes('star_nwk')
    nstar.addSeg(360,0,360,[(0,0),(0,100)])
    nstar.addSeg(90,0,90,[(0,0),(100,0)])
    nstar.addSeg(180,0,180,[(0,0),(0,-100)])
    nstar.addSeg(270,0,270,[(0,0),(-100,0)])
    assert Spoke(seg=nstar.segs[360],jct=nstar.jcts[360]).next().end().point == (0, -100)
    assert Spoke(seg=nstar.segs[270],jct=nstar.jcts[270]).next().end().point == (100, 0)
    assert Spoke(seg=nstar.segs[270],jct=nstar.jcts[0]).next() == None

    print 'pnwk_matchspokes test PASSED'

#doit
test()

