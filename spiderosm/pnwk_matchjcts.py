'''
Path Network - Match Jcts.
'''
import pdb

import geo 
import log
import misc
import pnwk_score

class PNwkMatchJcts(pnwk_score.PNwkScore):
    
    # match must be unique within both networks (for distance d)
    def jct_match_pass(self, otherNwk, d, filters):
        for jct in self.jcts.values():
                
            #skip previously merged junctions
            if jct.match: continue

            # must be unique match in own network, within d 
            self_match_set = self.JctMatchSet(set_nwk=self, jct=jct, aread=d, filter_list=filters)
            if len(self_match_set.set_jcts) !=1: continue
            assert self_match_set.set_jcts[0] == jct

            # must be unique match in other network, within d
            other_match_set = self.JctMatchSet(set_nwk=otherNwk, jct=jct, aread=d, filter_list=filters)
            if len(other_match_set.set_jcts) != 1: continue
            other_jct = other_match_set.set_jcts[0]

            # match!
            jct.match = other_jct
            other_jct.match = jct

    def match_stats(self, name=None, quiet=False):
        percent = misc.percent

        if not name: name = self.name
        num_segs = len(self.segs)
        num_jcts = len(self.jcts)
        miles = 0.0
        miles_matched = 0.0

        num_segs_matched = 0
        for seg in self.segs.values():
            miles += seg.length(units="miles")
            if seg.match != None: 
                num_segs_matched += 1
                miles_matched += seg.length(units="miles")
        percent_segs_matched= percent(num_segs_matched,num_segs)
        percent_miles_matched = percent(miles_matched,miles)

        num_jcts_matched = 0
        for jct in self.jcts.values():
            if jct.match != None: num_jcts_matched += 1
        percent_jcts_matched= percent(num_jcts_matched,num_jcts)
        if not quiet:
            line1 = '%s: jcts: %d/%d (%d%%) matched. segs: %d/%d (%d%%) matched.' % (
                name,
                num_jcts_matched, num_jcts, percent_jcts_matched,
                num_segs_matched, num_segs, percent_segs_matched)
            line2 = '%s: miles: %d/%d (%d%%) matched.' % (
                    name,
                    miles_matched,
                    miles,
                    percent_miles_matched)
            log.info('%s\n  %s', line1, line2)

        return {'num_jcts_matched':num_jcts_matched, 
                'num_jcts':num_jcts,
                'percent_jcts_matched':percent_jcts_matched,

                'num_segs_matched':num_segs_matched, 
                'num_segs':num_segs, 
                'percent_segs_matched':percent_segs_matched,

                'miles':miles,
                'miles_matched':miles_matched,
                'percent_miles_matched':percent_miles_matched}

    class JctMatchSet(object):
        def apply_filter(self, filter_func, parms):
            new_list = []
            for setJct in self.set_jcts:
                if filter_func(self, setJct, parms): new_list.append(setJct)
            self.set_jcts = new_list

        def apply_filters(self, filter_list):
            for filter_func,parms in filter_list:
                self.apply_filter(filter_func,parms)

        def __init__(self, set_nwk, jct, aread, filter_list):
            self.jct_nwk = jct.network
            self.jct = jct
            self.set_nwk = set_nwk
            self.set_jcts = set_nwk.get_jcts_near_point(jct.point, aread)
            self.apply_filters(filter_list)

        def jct_filter_two_names_in_common(self, setJct, parms):
            return len(setJct.names().intersection(self.jct.names())) >= 2

        # within max_d and no other point within d
        def jct_filter_max_d(self, setJct, parms):   
            (max_d,d) = parms

            #print 'DEBUG jct_filter_max_d max_d=%d' % max_d
            return (geo.distance(setJct.point,self.jct.point) <= max_d and
                    len(self.set_nwk.get_jcts_near_point(self.jct.point, d)) == 1)

def test_setup_g():
    g = PNwkMatchJcts('g')    
    g.add_seg(1, 10, 11, test_points, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])
    g.check()
    return g

def test_setup_n():
    g = PNwkMatchJcts('n')    
    g.add_seg(1, 10, 11, test_points2, names=['foo',
        "NE HALSEY ST FRONTAGE RD",
        "Northeast Halsey Street Frontage Road"])
    g.check()
    return g

test_points = [(0,0), (1000,1000)]
test_points2 = [(5,0), (1020,1000)]
def test():
    g = test_setup_g()

    n = test_setup_n()
    g.jct_match_pass(n, 40, [(g.JctMatchSet.jct_filter_max_d, (10,100))])
    stats = g.match_stats(quiet=True)
    #print 'stats', stats
    assert stats['num_jcts_matched'] == 1

    # don't choke on no matches.
    empty = PNwkMatchJcts('empty')
    stats=empty.match_stats(quiet=True)
    #print 'stats', stats
    assert stats['num_jcts_matched'] == 0

    print 'pnwk_matchjcts PASS'

#doit
if __name__ == "__main__":
    test()

