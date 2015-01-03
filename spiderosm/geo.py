'''
Geography / Geometry utilities.
'''

import math
import cmath
#import numpy

import pyproj
import shapely
import shapely.geometry

class Projection(object):
    def __init__(self,proj4text):
        # longlat = unprojected  ESPG:4326  (corresponds to OSM data)
        self.ll_proj = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        self.proj = pyproj.Proj(proj4text, preserve_units=True)

    # latlon -> local coords
    def project_point(self,p, rev=False):
        if rev: return pyproj.transform(self.proj, self.ll_proj, p[0], p[1])
        return pyproj.transform(self.ll_proj, self.proj, p[0], p[1])
  
    def project_box(self,box, rev=False):
        xmin,ymin,xmax,ymax = box
        pmin = self.project_point((xmin,ymin), rev=rev)
        pmax = self.project_point((xmax,ymax), rev=rev)
        return pmin + pmax
	
    # geo projections done in place
    def project_geo_linestring(self,ls, rev=False):
        new = []
        for p in ls['geometry']['coordinates']:
            new.append(self.project_point(p, rev=rev))
        ls['geometry']['coordinates'] = new

    def project_geo_features(self, geo, rev=False):
        for feature in geo:
            t = feature['geometry']['type']

            if t=='LineString': 
                self.project_geo_linestring(feature, rev=rev)
            else:
                # TODO other types. :)
                assert False

def _test_projection():
    proj = Projection('+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs')
    sf_geo = (-122.0,38.0)
    sf_utm = proj.project_point(sf_geo)
    sf_geo_roundtrip = proj.project_point(sf_utm, rev=True)
    epsilon = .000001
    #print 'sf_geo,sf_utm,sf_geo_roundtrip', sf_geo, sf_utm, sf_geo_roundtrip
    assert abs(sf_geo[0]-sf_geo_roundtrip[0]) < epsilon
    assert abs(sf_geo[1]-sf_geo_roundtrip[1]) < epsilon

# WKT
# Could use Shapely for this?
def wkt_point(point):
	return 'POINT (%.6f %.6f)' % point
def wkt_linestring(points):
	assert len(points)>1
	a = []
	for p in points: a.append('%.6f %.6f' % p)
	return 'LINESTRING (' + ', '.join(a) + ')'
def wkt_linestring_to_points(wkt_string):
    rx = re.compile(r"^\w*LINESTRING\w*\((.*)\)\w*$", re.IGNORECASE)
    point_string = rx.search(wkt_string).group(1)       
    coords = re.split(r"\s*,?\s*",point_string)
    assert len(coords)%2 == 0  # number of coords should be even!
    points=[]
    for i in xrange(0,len(coords),2):
        point = ( float(coords[i]), float(coords[i+1]) )
        points.append(point)
    return points

def shapely_point(point):
    return shapely.geometry.Point(point)

def shapely_linestring(points):
    return shapely.geometry.LineString(points)

def shapely_point_to_point(shapely_point):
    point_list = list(shapely_point.coords)
    assert len(point_list) == 1
    return point_list[0]
    
def shapely_linestring_to_points(shapely_linestring):
    return list(shapely_linestring.coords) 

def _test_shapely():
    p = (5,6.5)
    sp = shapely_point(p)
    pout = shapely_point_to_point(sp)
    assert p == pout

    ls = [(0,0),(1,10),(2,20)]
    sls = shapely_linestring(ls)
    lsout = shapely_linestring_to_points(sls)
    assert ls == lsout


# GEOMETRY

def buffer_box(box, amount):
    xmin,ymin,xmax,ymax = box
    xmin -= amount; ymin -= amount
    xmax += amount; ymax += amount
    return (xmin,ymin,xmax,ymax)

def distance(p0,p1):
	deltax= p1[0] - p0[0]
	deltay= p1[1] - p0[1]
	return abs(complex(deltax,deltay))

def _test_distance():
	assert distance((5,0),(15,0)) == 10
	assert distance((1,2),(4,6)) == 5

def length(points):
    d = 0
    prev = None
    for point in points:
        if prev: d += distance(prev,point)
        prev = point
    return d

def _test_length():
    assert length([]) == 0
    assert length([(5,10)]) == 0
    assert length([(0,0),(0,1)]) == 1
    assert length([(0,0),(0,1),(1,1),(1,0)]) == 3

# point along linestring distance d from beginning.
def interpolate(points,d):
    sls = shapely_linestring(points)
    spoint = sls.interpolate(d)
    return shapely_point_to_point(spoint)

def _test_interpolate():
    ls = [(0,0),(0,10),(10,10),(10,0),(0,0)]
    assert interpolate(ls, 5) == (0.0,5.0)
    assert interpolate(ls, 20) == (10.0,10.0)
    assert interpolate(ls, 39) == (1.0,0.0)

# returns (maxSep,avg_bearing_delta)
def divergence(points1, points2, delta=3):
    len1 = length(points1)
    len2 = length(points2)

    if len1<len2: 
        return divergence(points2,points1, delta=delta)
    assert len1 >= len2

    sls1 = shapely_linestring(points1)
    sls2 = shapely_linestring(points2)
    try:
        f = len2/len1
    except ZeroDivisionError:
        assert len1==0 and len2==0
        f= 1
    d1=0
    maxSep = 0
    p1_prev = None
    p2_prev = None
    num_b = 0
    cum_bdelta = 0
    while True:
        sp1 = sls1.interpolate(d1)
        sp2 = sls2.interpolate(d1*f)
        p1 = shapely_point_to_point(sp1)
        p2 = shapely_point_to_point(sp2)
        sep = sp1.distance(sp2)
        maxSep = max(maxSep,sep)

        if p1_prev:
            b1 = compass_bearing(p1_prev,p1)
            b2 = compass_bearing(p2_prev,p2)
            bdelta = compass_bearing_delta(b1,b2)
            cum_bdelta += bdelta
            num_b += 1 
        p1_prev = p1
        p2_prev = p2

        if d1==len1: break
        d1 += delta
        d1 = min(d1,len1)

    #print 'cum_bdelta', cum_bdelta
    #print 'num_b', num_b
    try:
        avg_bdelta = (cum_bdelta+0.0)/num_b
    except ZeroDivisionError:
        avg_bdelta = 0
    return (maxSep, avg_bdelta)

def _test_divergence():
    points1 = [(0,10),(100,15),(200,10)]
    points2 = [(0,-10),(100,-15),(200,-10)]
    points3 = [(0,0),(200,0)]
    points4 = [(0,0),(400,0)]
    assert 29 < divergence(points1,points2)[0] <= 30 
    assert divergence(points1,points1)[0] == 0
    assert 14 < divergence(points3,points1)[0] <= 15
    assert divergence(points3,points4)[0] == 200

    points5 = [(0,0),(20,20),(40,0),(400,0)]
    assert divergence(points3,points4)[1] == 0
    assert 5.7 < divergence(points4,points5,delta=10)[1] < 5.8

    points6 = [(0,0), (0,0)]
    points7 = [(10,0), (10,0)]
    assert divergence(points6,points7)[0] == 10 
    assert divergence(points6,points7)[1] == 0 

# distance along points nearest to point
def project(points,point):
    sls = shapely_linestring(points)
    sp = shapely_point(point)
    return sls.project(sp)

def _test_project():
    ls = [(0,0),(0,10),(10,10),(10,0),(0,0)]
    assert project(ls,(1,5)) == 5.0
    assert project(ls,(11,11)) == 20.0

def cut(points,d):
    assert 0 < d < length(points) 
    assert len(points)>=2
    part1 = []
    part2 = []
    curd = 0
    prev= None
    for p in points:
        if prev: curd += distance(prev,p)
        if curd<=d:
            part1.append(p)
        else:
            part2.append(p)
        prev = p

    if length(part1) != d:
        newp = interpolate(points,d)
        part1.append(newp)
        part2.insert(0,newp)
    else:
        part2.insert(0,part1[-1])

    return part1,part2

def _test_cut():
    points = [(0,1),(10,1),(20,1),(30,1)]
    part1,part2 = cut(points,5.0)
    #print 'part1:', part1
    #print 'part2:', part2
    assert len(part1)==2 and len(part2)==4
    part1,part2 = cut(points, 20.0)
    #print 'part1:', part1
    #print 'part2:', part2
    assert len(part1)==3 and len(part2)==2

def point_in_rect_q(point, rect):
    px,py = point
    x0,y0,x1,y1 = rect
    return x0<=px<x1 and y0<=py<y1

def _test_point_in_rect_q():
    assert point_in_rect_q((1,2),(0,0,10,10))
    assert not point_in_rect_q((100,2),(0,0,10,10))

# does at least one of the points fall inside rect?
def points_intersect_rect_q(points, rect):
    for point in points:
        if point_in_rect_q(point, rect): return True
    return False

def _test_points_intersect_rect_q():
    assert not points_intersect_rect_q([(100,1),(200,2),(300,3)], (0,0,10,10)) 
    assert points_intersect_rect_q([(100,1),(2,2),(300,3)], (0,0,10,10)) 

def compass_bearing(p0,p1):
	deltax = p1[0] - p0[0]
	deltay = p1[1] - p0[1]
	theta = math.degrees(cmath.phase(complex(deltax,deltay)))
	bearing = 90-theta
	if bearing<0 : bearing += 360
	return bearing

def compass_bearing_delta(bearing0, bearing1):
    delta = bearing0-bearing1
    delta = abs(delta) % 360
    if delta>180: delta = 360-delta
    #print 'cbd:', bearing0, bearing1, delta
    return delta

def _test_compass_bearing():
	cb=compass_bearing
	assert cb((0,0),(0,1)) == 0
	assert cb((0,0),(10,0)) == 90
	assert cb((0,0),(0,-110)) == 180
	assert cb((0,1),(-11,1)) == 270
	assert cb((5,10),(5,20)) == 0

def _test_compass_bearing_delta():
    bd= compass_bearing_delta
    assert bd(350,10) == 20
    assert bd(10,350) == 20
    assert bd(-90,90) == 180
    assert bd(0,340) == 20

class BBox(object):
    def __init__(self):
        self.box = None

    def rect(self):
        return self.box

    def add_point(self,point):
        x,y = point
        if not self.box:
            self.box = (x,y,x,y)
        else:
            x0,y0,x1,y1 = self.box
            self.box = (min(x0,x),min(y0,y),max(x1,x),max(y1,y))

    def add_points(self,points):
        for point in points: self.add_point(point)

def _test_BBox():
    bb = BBox()
    assert bb.rect() == None
    bb.add_point((10,100))
    assert bb.rect() == (10,100,10,100)
    bb.add_point((-5,120))
    assert bb.rect() == (-5, 100, 10, 120)
    bb.add_points([(0,0), (105,105), (-10,-10)])
    assert bb.rect() == (-10, -10, 105, 120)

def _test_linestring_to_points():
    ls = 'LINESTRING(1.1,10.0 2.2, 20.0)'
    points = wkt_linestring_to_points(ls)
    assert len(points) == 2
    assert points[1][0] == 2.2 and points[1][1] == 20.0

def _test_linestring_conversions():
    wkt_in = "LINESTRING(7696992.83333333 682678.163713917,7696997.45603675 682808.892060369)"
    print 'wkt_in:', wkt_in
    points = wkt_linestring_to_points(wkt_in)
    print 'points:', points
    wkt_out = wkt_linestring(points)
    print 'wkt_out:', wkt_out

def test():
        #test_linestring_to_points()
        _test_projection()
	_test_distance()
        _test_length()
        _test_divergence()
	_test_compass_bearing()
        _test_compass_bearing_delta()
        _test_point_in_rect_q()
        _test_points_intersect_rect_q()
        _test_BBox()
        _test_shapely()
        _test_interpolate()
        #_test_project()
        _test_cut()
	print 'geo PASS'

#doit
if __name__ == "__main__":
    test()

