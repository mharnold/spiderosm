'''
Path Network - Match Jcts.
'''
import pdb

import geo 
import names as canNames
import pnwk_score

class PNwkMatchJcts(pnwk_score.PNwkScore):
    
    # match must be unique within both networks (for distance d)
    def jctMatchPass(self, otherNwk, d, filters):
        for jct in self.jcts.values():
                
            #skip previously merged junctions
            if jct.match: continue

            # must be unique match in own network, within d 
            selfMatchSet = self.JctMatchSet(setNwk=self, jct=jct, aread=d, filterList=filters)
            if len(selfMatchSet.setJcts) !=1: continue
            assert selfMatchSet.setJcts[0] == jct

            # must be unique match in other network, within d
            otherMatchSet = self.JctMatchSet(setNwk=otherNwk, jct=jct, aread=d, filterList=filters)
            if len(otherMatchSet.setJcts) != 1: continue
            other_jct = otherMatchSet.setJcts[0]

            # match!
            jct.match = other_jct
            other_jct.match = jct

    def matchStats(self, name=None, quiet=False):
        if not name: name = self.name
        numSegs = len(self.segs)
        numJcts = len(self.jcts)
        miles = 0.0
        milesMatched = 0.0

        numSegsMatched = 0
        for seg in self.segs.values():
            miles += seg.length(units="miles")
            if seg.match != None: 
                numSegsMatched += 1
                milesMatched += seg.length(units="miles")
        percentSegsMatched= (100*numSegsMatched)/numSegs
        percentMilesMatched = round(100*milesMatched/miles)

        numJctsMatched = 0
        for jct in self.jcts.values():
            if jct.match != None: numJctsMatched += 1
        percentJctsMatched= (100*numJctsMatched)/numJcts
        if not quiet:
            print '%s: jcts: %d/%d (%d%%) matched. segs: %d/%d (%d%%) matched.' % (
                name,
                numJctsMatched, numJcts, (100*numJctsMatched)/numJcts,
                numSegsMatched, numSegs, (100*numSegsMatched)/numSegs)
            print '%s: miles: %d/%d (%d%%) matched.' % (
                    name,
                    milesMatched,
                    miles,
                    percentMilesMatched)

        return {'numJctsMatched':numJctsMatched, 
                'numJcts':numJcts,
                'percentJctsMatched':percentJctsMatched,

                'numSegsMatched':numSegsMatched, 
                'numSegs':numSegs, 
                'percentSegsMatched':percentSegsMatched,

                'miles':miles,
                'milesMatched':milesMatched,
                'percentMilesMatched':percentMilesMatched}

    class JctMatchSet(object):
        def apply_filter(self, filterFunc, parms):
            newList = []
            for setJct in self.setJcts:
                if filterFunc(self, setJct, parms): newList.append(setJct)
            self.setJcts = newList

        def apply_filters(self, filterList):
            for filterFunc,parms in filterList:
                self.apply_filter(filterFunc,parms)

        def __init__(self, setNwk, jct, aread, filterList):
            self.jctNwk = jct.network
            self.jct = jct
            self.setNwk = setNwk
            self.setJcts = setNwk.getJctsNearPoint(jct.point, aread)
            self.apply_filters(filterList)

        def jctFilterTwoNamesInCommon(self, setJct, parms):
            return len(setJct.names().intersection(self.jct.names())) >= 2

        # within maxd and no other point within d
        def jctFilterMaxD(self, setJct, parms):   
            (maxd,d) = parms

            #print 'DEBUG jctFilterMaxD maxd=%d' % maxd
            return (geo.distance(setJct.point,self.jct.point) <= maxd and
                    len(self.setNwk.getJctsNearPoint(self.jct.point, d)) == 1)

def testSetupG():
    g = PNwkMatchJcts('g')    
    g.addSeg(1, 10, 11, test_points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])
    g.check()
    return g

def testSetupN():
    g = PNwkMatchJcts('n')    
    g.addSeg(1, 10, 11, test_points2, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])
    g.check()
    return g

test_points = [(0,0), (1000,1000)]
test_points2 = [(5,0), (1020,1000)]
def test():
    g = testSetupG()
    n = testSetupN()
    g.jctMatchPass(n, 40, [(g.JctMatchSet.jctFilterMaxD, (10,100))])
    stats = g.matchStats(quiet=True)
    #print 'stats', stats
    assert stats['numJctsMatched'] == 1
    print 'pnwk_matchjcts test PASSED'

#doit
test()

