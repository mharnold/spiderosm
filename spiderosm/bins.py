'''
Implements simmple two dimensional bin system for objects 'indexed' by points: (x,y)
'''

import math

import geo

class Bins(object):
    def __init__(self,diameter):
        self.diameter = diameter
        self.bins = {}

    def _index(self,coord):
        return int(math.floor(coord/self.diameter))

    def _index2(self,point):
        x,y = point
        return (self._index(x), self._index(y))

    def add(self,point,value):
        bin = self.bins.setdefault(self._index2(point),[])
        bin.append((point,value))

    def in_rect(self,rect):
        x0,y0,x1,y1 = rect
        ix0 = self._index(x0)
        iy0 = self._index(y0)
        ix1 = self._index(x1)
        iy1 = self._index(y1)

        results = []
        for ix in range(ix0,ix1+1):
            for iy in range (iy0,iy1+1):
                if self.bins.has_key((ix,iy)):
                    for point,value in self.bins[(ix,iy)]:
                        if geo.point_in_rect_q(point, rect): results.append((point,value))
        return results

    def in_radius(self,point,r):
        px,py = point
        results = []
        for p2,value in self.in_rect((px-r,py-r,px+r,py+r)):
            if geo.distance(point,p2) < r: results.append((p2,value))
        return results
        
def test():
    b = Bins(100)
    b.add((1,1),'a')
    b.add((2,3),'b')
    b.add((1000,1000000),'far')
    assert len(b.in_rect((0,0,50,50))) == 2 
    assert len(b.in_rect((800,999000,1200,1001000))) == 1
    assert len(b.in_radius((1,1),0.5)) == 1
    assert len(b.in_radius((1,1),100)) == 2
    assert len(b.in_radius((1001,1000001),10)) == 1
    assert len(b.in_radius((-1,0),.1)) == 0

    print 'bins PASS'

#doit
if __name__ == "__main__":
    test()

