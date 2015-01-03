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
    def spoke_crawl(self, star_jct_match_list, msg=None, quiet=False):
        #if msg and not quiet: print 'SPOKECRAWL:',msg
        new_jct_matches = star_jct_match_list
        passNum = 0
        while len(new_jct_matches)>0:
            passNum += 1
            #if not quiet: 
            if False:
                print 'pass %d, processing %d matched junctions:' % (passNum, len(new_jct_matches))
            new_jct_matches = match_spokes(new_jct_matches)

        return passNum>1

class Spoke(object):
    def __init__(self, jct, seg):
        assert jct.network == seg.network
        self.jct = jct
        self.seg = seg

        if seg.from_jct == jct:
            self.bearing = seg.from_bearing
        else:
            assert seg.to_jct == jct
            self.bearing = seg.to_bearing

    # is spoke direction reversed from segment direction
    def upstream(self):
        return self.seg.to_jct == self.jct

    # return jct at far end of spoke
    def end(self):
        return self.seg.other_end(self.jct)

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
    def trim(self,d,new_jct_id=None):
        assert 0<d and d<self.length()
        fromBeginning = not self.upstream()
        self.seg.split(d, fromBeginning, new_jct_id=new_jct_id) 
        assert not new_jct_id or self.end().jct_id==new_jct_id

    # return subset of spokes that match self (along with distances along spokes of match)
    def match(self, spokes):
        match_set = []
        if self.seg.match: return match_set

        len1 = self.length()
        street_scale = self.seg.network.street_scale
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
            if abs(d1-d2) > max(street_scale, 0.1*length): continue

            # to match, segment end points must be near each other
            if geo.distance(self.interpolate(d1),spoke.interpolate(d2)) > street_scale: continue

            match_set.append((self, d1, spoke, d2))

        return match_set
 
def _trim_spoke_q(shorter, longer, d):

    # if length difference significant, trim
    if abs(longer.length()-d)>longer.seg.network.street_scale:
        return True 
   
    # if next point after shorter spoke end is better match for longer end, trim!
    next_shorter = shorter.next()
    if next_shorter:
        delta_next = geo.distance(longer.end().point, next_shorter.end().point)
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
    if _trim_spoke_q(shorter, longer, d):
        longer.trim(d)
        shorter.end().tags['export_count'] = shorter.end().tags.get('export_count',0) + 1
        longer.end().tags['import_src'] = shorter.end()

def _match_jct_spokes(jct1, jct2):
    global there
    assert jct1.network != jct2.network
    new_jct_matches = []
    
    spokes1 = jct1.spokes()
    spokes2 = jct2.spokes()
    #print 'len1, len2:', len(spokes1), len(spokes2)

    for spoke1 in spokes1:
        match_set = spoke1.match(spokes2)
        
        #matches must be unique
        if len(match_set) != 1: continue

        spoke1x,d1,spoke2,d2 = match_set[0]
        assert spoke1x == spoke1

        #matches must be unique in both directions
        match_set2 = spoke2.match(spokes1)
        assert spoke1 in [ m[2] for m in match_set2 ]
        if len(match_set2) != 1: continue

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
        spoke1.seg.match_rev = rev
        spoke2.seg.match_rev = rev

        # continue spoke crawl where we left off.
        new_jct_matches.append((spoke1.end(), spoke2.end()))
        there = False

    return new_jct_matches

def match_spokes(jct_match_list):
    new_jct_matches = []
    for (jct1,jct2) in jct_match_list:
        new_jct_matches += _match_jct_spokes(jct1, jct2)
    return new_jct_matches


def test():
    points = [(0,0), (1000,1000)]
    points2 = [(5,0), (1005,1000)]
    g = PNwkMatchSpokes('g')    
    g.add_seg(1, 10, 11, points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])

    # test spokes
    spokes = g.jcts[10].spokes()
    assert len(spokes)==1 and spokes[0].bearing==45 and spokes[0].seg.seg_id==1 
    spokes = g.jcts[11].spokes()
    assert len(spokes)==1 and spokes[0].bearing==225 and spokes[0].seg.seg_id==1 
    g.check()

    # test segment and spoke length
    n3 = PNwkMatchSpokes('n3_nwk')
    points3 = [(0,0),(1,0),(1,1)]
    n3.add_seg(1, 10, 11, points3)
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
    nstar.add_seg(360,0,360,[(0,0),(0,100)])
    nstar.add_seg(90,0,90,[(0,0),(100,0)])
    nstar.add_seg(180,0,180,[(0,0),(0,-100)])
    nstar.add_seg(270,0,270,[(0,0),(-100,0)])
    assert Spoke(seg=nstar.segs[360],jct=nstar.jcts[360]).next().end().point == (0, -100)
    assert Spoke(seg=nstar.segs[270],jct=nstar.jcts[270]).next().end().point == (100, 0)
    assert Spoke(seg=nstar.segs[270],jct=nstar.jcts[0]).next() == None

    print 'pnwk_matchspokes PASS'

#doit
if __name__ == "__main__":
	test()
