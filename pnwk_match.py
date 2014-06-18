'''
Path Network - Matcher
'''
import pdb

import geo 
import pnwk_matchspokes

class PNwkMatch(pnwk_matchspokes.PNwkMatchSpokes):
        
    # match into nwk2 
    # matches are searched for in radius d and must be unique within that radius in both networks
    def match(self, nwk2, maxd=None, d=None, quiet=False):
        if not maxd:
            assert self.streetScale == nwk2.streetScale
            maxd = self.streetScale
        if not d:
            assert self.blockScale == nwk2.blockScale
            d = self.blockScale / 3.0

        #TODO remove or restore maxd,d

        # Check network consistency
        self.check()
        nwk2.check()

        # Initial stats
        statsBefore = nwk2.matchStats(quiet=True)

        # Identify corresponding junctions as launch points for spoke crawling.
        #
        # It's more important to be certain of matches, then to be comprehensive:
        # spoke crawling will fill in the gaps.
        self.jctMatchPass(nwk2, d, [(self.JctMatchSet.jctFilterMaxD, (maxd,d))])

        # Crawl out from matched juctions along 'spokes'
        # NOTE INITIAL jct matches are one <-> one.  But not true in general.
        newJctMatches = []
        for jct in nwk2.jcts.values():
            if jct.match: newJctMatches.append((jct.match, jct))
        #print 'DEBUG initial newJctMatches:', newJctMatches
        self.spokeCrawl(newJctMatches, msg='crawling from initial matched junctions')

        # try (re)crawling out from matched segment end points
        progress = True
        crawl = 0
        while progress:
            crawl += 1
            newJctMatches = []
            for seg in self.segs.values():
                if not seg.match: continue
                if seg.matchRev:
                    newJctMatches.append((seg.fromJct,seg.match.toJct))
                    newJctMatches.append((seg.toJct,seg.match.fromJct))
                else:
                    newJctMatches.append((seg.fromJct,seg.match.fromJct))
                    newJctMatches.append((seg.toJct,seg.match.toJct))
            progress = self.spokeCrawl(
                    newJctMatches, 
                    msg='(re)craw number %d, from matched segment end points' % crawl
                    )
            
        # Progress stats 
        statsAfter = nwk2.matchStats(quiet=True)
        numSegsMatched = statsAfter['numSegsMatched']
        delta = statsAfter['numSegsMatched'] - statsBefore['numSegsMatched']
        if not quiet: print '===== new segs matches: %d, total seg matches: %d' % (
            delta, numSegsMatched)

        # Score matches
        self.scoreMatches()
        
        # share attributes of matched segs and jcts
        for seg in self.segs.values():
            if seg.match: 
                seg.tags.update(seg.match._asdict())
                seg.match.tags.update(seg._asdict())
        for jct in self.jcts.values():
            if jct.match: 
                jct.tags.update(jct.match.tags)
                jct.match.tags.update(seg.tags)

        # Check network consistency
        self.check()
        nwk2.check()

def test():
    points = [(0,0), (1000,1000)]
    points2 = [(5,0), (1005,1000)]
    g = PNwkMatch('g')    
    g.addSeg(1, 10, 11, points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])

    # test match
    n2 = PNwkMatch('n2_nwk')
    n2.addSeg(segId=100, fromJctId=1000, toJctId=1100, points=points2, names=['bar'])
    g.match(n2, quiet=True)
    stats = g.matchStats(quiet=True)
    #stats = g.matchStats(quiet=False)
    assert stats['numJctsMatched'] == 2 and stats['numSegsMatched'] == 1
    assert g.segs[1].match == n2.segs[100]   
    assert n2.segs[100].matchRev == 0
    g.check()
   
    print 'pnwk_match test PASSED'

#doit
test()

