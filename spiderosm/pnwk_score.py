'''
Path Network - Match Scoring
'''

import geo 
import cannames
import pnwk_network

def _prob_to_score(p):
    assert 0 <= p <= 1
    return round(100*p)

class PNwkScore(pnwk_network.PNwkNetwork):
    def score_matches(self):
        for seg in self.segs.values(): 
            seg.score_match()

    class Seg(pnwk_network.PNwkNetwork.Seg):
        def _score_name_match(self):
            if not self.match: return
            if len(self.names)==0 or len(self.match.names)==0: return
            self._set_score('score_name', cannames.match_score(self.names,self.match.names))

        def _score_geo_match(self):
            if not self.match: return
            f = self.network.units_per_meter
            delta = 3.0*f # distance between samples
            if self.match_rev:
                (div,avg_bearing_delta) = geo.divergence(self.points,self.match.points[::-1],delta)
            else:
                (div, avg_bearing_delta) = geo.divergence(self.points,self.match.points,delta)

            # p1 based on divergence  (div of 30 meters or more scores 0)
            p1 = 1.0 - min(div/f,30.0)/30.0
            #print 'p1,div', p1, div

            # p2 based on ratio of divergenece to segment length
            length = min(self.length(),self.match.length())
            if(length<self.network.stepScale): 
                p2 = 0.0
            else:
                p2 = max(0,1.0-div/length)

            score = round(p1*p2*100.0)
            #print 'seg_id,length,div,p1,p2,geoScore',self.seg_id,length,div,p1,p2,score
            self._set_score('divergence', div)
            self._set_score('avg_bearing_delta', avg_bearing_delta)
            self._set_score('score_bearing1', _prob_to_score(1.0 - avg_bearing_delta/180.0))
            self._set_score('score_geo1', _prob_to_score(p1))
            self._set_score('score_geo2', _prob_to_score(p2))

        def _score_bearing_match(self):
            if not self.match: return
            if self.match_rev:
                delta1 = geo.compass_bearing_delta(self.from_bearing,self.match.to_bearing)
                delta2 = geo.compass_bearing_delta(self.to_bearing,self.match.from_bearing)
            else:
                delta1 = geo.compass_bearing_delta(self.from_bearing,self.match.from_bearing)
                delta2 = geo.compass_bearing_delta(self.to_bearing,self.match.to_bearing)

            p1 = 1 - (delta1/180.0)
            p2 = 1 - (delta2/180.0)
            self._set_score('score_bearing2', _prob_to_score(p1*p2))


        def _set_score(self,key,value):
            ns = self.network.match_namespace
            self.tags[ns+key] = value

        def _score_to_factor(self,key,importance=1.0):
            ns = self.network.match_namespace
            key =  ns + key
            if key in self.tags:
                score = self.tags[key]
            else:
                score = 50
            f = float(score)/100.0
            fscaled = (1.0-importance) + importance*f 
            return fscaled

        def score_combine(self,
                score_name_i=0.20,
                score_geo1_i=0.50,
                score_geo2_i=0.50,
                score_bearing1_i=0.50,
                score_bearing2_i=0.50):
            p = (self._score_to_factor('score_name',importance=score_name_i) *
                    self._score_to_factor('score_geo1',importance=score_geo1_i) *
                    self._score_to_factor('score_geo2',importance=score_geo2_i) *
                    self._score_to_factor('score_bearing1',importance=score_bearing1_i) *
                    self._score_to_factor('score_bearing2',importance=score_bearing2_i)
                    )
            return _prob_to_score(p)

        def score_match(self, name_importance=0.20):
            if not self.match: return
            self._score_name_match()
            self._score_geo_match()
            self._score_bearing_match()
            self._set_score('score', self.score_combine())

def test():
    
    # _prob_to_score()
    assert _prob_to_score(0)==0 and _prob_to_score(1)==100 and _prob_to_score(.25)==25 and _prob_to_score(.007)==1

    # test _score_to_factor
    class SegStub(PNwkScore.Seg):
        def __init__(self):
            self.tags={}
    segy = SegStub()
    segy.network = PNwkScore(name='t')
    segy._set_score('0',0)
    segy._set_score('50',50)
    segy._set_score('75',75)
    segy._set_score('80',80)
    segy._set_score('100',100)
    assert segy.tags['match$50']==50
    assert segy._score_to_factor('75') == .75
    assert segy._score_to_factor('not_there') == .50
    assert segy._score_to_factor('0',importance=.1) == .90
    assert segy._score_to_factor('100',importance=.1) == 1.00 
    assert segy._score_to_factor('80',importance=.1) == .98
    assert segy._score_to_factor('not_there',importance=.80) == .60

    print 'pnwk_score PASS'

#doit
if __name__ == "__main__":
    test()
