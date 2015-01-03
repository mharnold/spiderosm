'''
Path Network - Matcher
'''
import pdb

import geo 
import pnwk_matchspokes

class PNwkMatch(pnwk_matchspokes.PNwkMatchSpokes):
        
    # match into nwk2 
    # matches are searched for in radius d and must be unique within that radius in both networks
    def match(self, nwk2, max_d=None, d=None, quiet=False):
        if not max_d:
            assert self.street_scale == nwk2.street_scale
            max_d = self.street_scale
        if not d:
            assert self.block_scale == nwk2.block_scale
            d = self.block_scale / 3.0

        #TODO remove or restore max_d,d

        # Check network consistency
        self.check()
        nwk2.check()

        # Initial stats
        statsBefore = nwk2.match_stats(quiet=True)

        # Identify corresponding junctions as launch points for spoke crawling.
        #
        # It's more important to be certain of matches, then to be comprehensive:
        # spoke crawling will fill in the gaps.
        self.jct_match_pass(nwk2, d, [(self.JctMatchSet.jct_filter_max_d, (max_d,d))])

        # Crawl out from matched juctions along 'spokes'
        # NOTE INITIAL jct matches are one <-> one.  But not true in general.
        new_jct_matches = []
        for jct in nwk2.jcts.values():
            if jct.match: new_jct_matches.append((jct.match, jct))
        #print 'DEBUG initial new_jct_matches:', new_jct_matches
        self.spoke_crawl(new_jct_matches, 
                msg='crawling from initial matched junctions',
                quiet=quiet)

        # try (re)crawling out from matched segment end points
        progress = True
        crawl = 0
        while progress:
            crawl += 1
            new_jct_matches = []
            for seg in self.segs.values():
                if not seg.match: continue
                if seg.match_rev:
                    new_jct_matches.append((seg.from_jct,seg.match.to_jct))
                    new_jct_matches.append((seg.to_jct,seg.match.from_jct))
                else:
                    new_jct_matches.append((seg.from_jct,seg.match.from_jct))
                    new_jct_matches.append((seg.to_jct,seg.match.to_jct))
            progress = self.spoke_crawl(new_jct_matches, 
                    msg='(re)craw number %d, from matched segment end points' % crawl,
                    quiet=quiet
                    )
            
        # Progress stats 
        statsAfter = nwk2.match_stats(quiet=True)
        num_segs_matched = statsAfter['num_segs_matched']
        delta = statsAfter['num_segs_matched'] - statsBefore['num_segs_matched']
        #if not quiet: 
        if False:
            print '===== new segs matches: %d, total seg matches: %d' % (
            delta, num_segs_matched)

        # Score matches
        self.score_matches()
        
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
    g.add_seg(1, 10, 11, points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])

    # test match
    n2 = PNwkMatch('n2_nwk')
    n2.add_seg(seg_id=100, from_jct_id=1000, to_jct_id=1100, points=points2, names=['bar'])
    g.match(n2, quiet=True)
    stats = g.match_stats(quiet=True)
    #stats = g.match_stats(quiet=False)
    assert stats['num_jcts_matched'] == 2 and stats['num_segs_matched'] == 1
    assert g.segs[1].match == n2.segs[100]   
    assert n2.segs[100].match_rev == 0
    g.check()
   
    print 'pnwk_match PASS'

#doit
if __name__ == "__main__":
    test()
