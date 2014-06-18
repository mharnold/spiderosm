'''
Path Network - Match Scoring
'''

import geo 
import cannames
import pnwk_network

def prob2score(p):
    assert 0 <= p <= 1
    return round(100*p)

class PNwkScore(pnwk_network.PNwkNetwork):
    def scoreMatches(self):
        for seg in self.segs.values(): 
            seg.scoreMatch()

    class Seg(pnwk_network.PNwkNetwork.Seg):
        def scoreNameMatch(self):
            if not self.match: return
            if len(self.names)==0 or len(self.match.names)==0: return
            self.setScore('scoreName', cannames.match_score(self.names,self.match.names))

        def scoreGeoMatch(self):
            if not self.match: return
            if self.matchRev:
                (div,avgBearingDelta) = geo.divergence(self.points,self.match.points[::-1])
            else:
                (div, avgBearingDelta) = geo.divergence(self.points,self.match.points)

            # p1 based on divergence
            p1 = 1.0 - min(div,100.0)/100.0
            #print 'p1,div', p1, div

            # p2 based on ratio of divergenece to segment length
            length = min(self.length(),self.match.length())
            if(length<self.network.stepScale): 
                p2 = 0.0
            else:
                p2 = max(0,1.0-div/length)

            score = round(p1*p2*100.0)
            #print 'segId,length,div,p1,p2,geoScore',self.segId,length,div,p1,p2,score
            self.setScore('divergence', div)
            self.setScore('avgBearingDelta', avgBearingDelta)
            self.setScore('scoreBearing1', prob2score(1.0 - avgBearingDelta/180.0))
            self.setScore('scoreGeo1', prob2score(p1))
            self.setScore('scoreGeo2', prob2score(p2))

        def scoreBearingMatch(self):
            if not self.match: return
            if self.matchRev:
                delta1 = geo.compass_bearing_delta(self.fromBearing,self.match.toBearing)
                delta2 = geo.compass_bearing_delta(self.toBearing,self.match.fromBearing)
            else:
                delta1 = geo.compass_bearing_delta(self.fromBearing,self.match.fromBearing)
                delta2 = geo.compass_bearing_delta(self.toBearing,self.match.toBearing)

            p1 = 1 - (delta1/180.0)
            p2 = 1 - (delta2/180.0)
            self.setScore('scoreBearing2', prob2score(p1*p2))


        def setScore(self,key,value):
            ns = self.network.matchNameSpace
            self.tags[ns+key] = value

        def score2factor(self,key,importance=1.0):
            ns = self.network.matchNameSpace
            key =  ns + key
            if key in self.tags:
                score = self.tags[key]
            else:
                score = 50
            f = float(score)/100.0
            fscaled = (1.0-importance) + importance*f 
            return fscaled

        def scoreCombine(self,
                scoreNameI=0.20,
                scoreGeo1I=0.50,
                scoreGeo2I=0.50,
                scoreBearing1I=0.50,
                scoreBearing2I=0.50):
            p = (self.score2factor('scoreName',importance=scoreNameI) *
                    self.score2factor('scoreGeo1',importance=scoreGeo1I) *
                    self.score2factor('scoreGeo2',importance=scoreGeo2I) *
                    self.score2factor('scoreBearing1',importance=scoreBearing1I) *
                    self.score2factor('scoreBearing2',importance=scoreBearing2I)
                    )
            return prob2score(p)

        def scoreMatch(self, nameImportance=0.20):
            if not self.match: return
            self.scoreNameMatch()
            self.scoreGeoMatch()
            self.scoreBearingMatch()
            self.setScore('score', self.scoreCombine())

def test():
    
    # prob2score()
    assert prob2score(0)==0 and prob2score(1)==100 and prob2score(.25)==25 and prob2score(.007)==1

    # test score2factor
    class SegStub(PNwkScore.Seg):
        def __init__(self):
            self.tags={}
    segy = SegStub()
    segy.network = PNwkScore(name='t')
    segy.setScore('0',0)
    segy.setScore('50',50)
    segy.setScore('75',75)
    segy.setScore('80',80)
    segy.setScore('100',100)
    assert segy.tags['match$50']==50
    assert segy.score2factor('75') == .75
    assert segy.score2factor('not_there') == .50
    assert segy.score2factor('0',importance=.1) == .90
    assert segy.score2factor('100',importance=.1) == 1.00 
    assert segy.score2factor('80',importance=.1) == .98
    assert segy.score2factor('not_there',importance=.80) == .60

    print 'pnwk_score PASS'

#doit
test()

