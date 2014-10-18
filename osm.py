import os
import time
import shutil
import urllib
import math
import cmath

import pyproj
import imposm.parser  # parses OpenStreetMaps xml and pbf file formats.
import geojson

import geo
import pnwk

osm_geojson_file_extension = '.osm.geojson'

class Way(object):
    def __init__(self, tags, node_ids):
        self.tags = tags
        self.node_ids = node_ids

class Node(object):
    def __init__(self, coords, tags=None):
        self.coords = coords
        self.tags = tags or {}       
        self.way_ids = {} # keys are way_ids of ways referencing this node.  values are ref counts.

class OSMData(object):
    ways = {}
    nodes = {}
    #relations = {} CURRENTLY NOT PARSING RELATIONS.

    def _parse_node(self, osmId, coords, tags=None):
        if self.proj: coords = self.proj.project_point(coords)
        if self.clip_rect and not geo.point_in_rect_q(coords,self.clip_rect): return
	self.nodes[osmId] = Node(coords, tags=tags)
        #if tags: print 'DEB _parse_node, osmId:',osmId,'tags:',tags

    # callback for coords (called for ALL nodes, both those with and without tags.)
    def _parse_coords(self, coords_in):
        for osmId, lon, lat in coords_in:
	    if not (osmId in self.nodes): self._parse_node(osmId, (lon,lat))

    # callback for nodes (with tags only)
    def _parse_nodes(self, nodes_in):
	for osmId,tags,coords in nodes_in:
            self._parse_node(osmId, coords, tags=tags)
       
    # callback for ways
    def _parse_ways(self, ways_in):
        for osmid, tags, refs in ways_in:

	    # roads only
	    if not ('highway' in tags): continue
            
            # at least two nodes (in clip area)
            count = 0
            for ref in refs:
                if ref in self.nodes: 
                    count += 1
                    if count >= 2: break
            if count < 2: continue

            # remove refs to missing nodes
            new = []
            for ref in refs:
                if ref in self.nodes: new.append(ref)
            refs = new

	    self.ways[osmid] = Way(tags=tags, node_ids=refs)		
 
    # read in an OSM data file
    # processing in two passes to avoid thrashing when clipping an area from huge files.
    def _parse_input_file(self, file_name):

        # first pass: nodes 
	p = imposm.parser.OSMParser(
	    coords_callback=self._parse_coords,
	    nodes_callback=self._parse_nodes)
				
	print 'Reading nodes from osm file:', file_name
	if os.path.splitext(file_name)[1] == '.xml':
	    p.parse_xml_file(file_name)
	else:
	    p.parse(file_name)

        # second pass: ways
	p = imposm.parser.OSMParser(
	    ways_callback=self._parse_ways)
				
	print 'Reading ways from osm file:', file_name
	if os.path.splitext(file_name)[1] == '.xml':
	    p.parse_xml_file(file_name)
	else:
	    p.parse(file_name)
	    
	print 'len(ways):', len(self.ways)
	print 'len(nodes):', len(self.nodes)

    # remove stutters (repeated node refs) from ways
    def _remove_stutters(self):
        num_removed = 0
        for way_id in self.ways:
            new = []
            for ref in self.ways[way_id].node_ids:
                if len(new) > 0 and ref == new[-1]:
                    print 'DELETING REPEATED NODE REFERENCE %d from way %d' % (ref, way_id)
                    num_removed += 1
                else:
                    new.append(ref)
            self.ways[way_id].node_ids = new 
        if num_removed>0: print 'REMOVED %d REPEATED NODE REFERENCES.' % num_removed

    # remove ways with less than two nodes left (after stutter removal.)
    def _remove_malformed_ways(self):
        num_removed = 0
        for way_id in self.ways.keys():
            if len(self.ways[way_id].node_ids) < 2: del self.ways[way_id]

    # add referencing ways to nodes
    def _add_refs_to_nodes(self):
	for way_id,way in self.ways.items():
	    for node_id in way.node_ids:
		node = self.nodes[node_id]
                # node.way_ids keys are ids for referencing Ways, value is ref count for that way.
		if way_id in node.way_ids: 
		    node.way_ids[way_id] += 1
		else: 
		    node.way_ids[way_id] = 1		
                    
    # delete nodes that have no tags and no refs
    def _vacuum_nodes(self):
	for node_id,node in self.nodes.items():
	    if len(node.tags)==0 and len(node.way_ids)==0: 
	        del self.nodes[node_id]
		#print 'del node:',node_id

    # initialize from OSM input file
    def __init__(self, file_name, clip_rect=None, target_proj=None):
        self.clip_rect = clip_rect

        self.proj=None
        if target_proj: self.proj = geo.Projection(target_proj)
       
	#read in file
	self._parse_input_file(file_name)

        #remove stutters from ways (repeated node refs)
        self._remove_stutters()

        # remove any ways with less than two nodes left.
        self._remove_malformed_ways()

	# add way references to nodes
	self._add_refs_to_nodes()

	# remove nodes that have neither tags nor are referenced by ways
	self._vacuum_nodes()
	print 'len(nodes) after vacuum:', len(self.nodes)

	# count intersections
	numi = 0
	for id,node in self.nodes.items():
	    if len(node.way_ids)>1: numi += 1
	print 'intersections:', numi

    def node_geo(self,node_id):
        node = self.nodes[node_id]
        geometry = geojson.Point(node.coords)
        properties = { 'nodeId' : node_id }
        properties.update(node.tags)
        return geojson.Feature(geometry=geometry, id=node_id, properties=properties)

    def way_geo(self, way_id):
        way = self.ways[way_id]
        points = [self.nodes[node_id].coords for node_id in way.node_ids]
        geometry = geojson.LineString(points)
        properties = {'way_id' : way_id}
        properties.update(way.tags)
        return geojson.Feature(geometry=geometry, id=way_id, properties=properties)
    
    @property
    def __geo_interface__(self):
        features = []
        for way_id in self.ways.keys():
            features.append(self.way_geo(way_id))
        for node_id in self.nodes.keys():
            features.append(self.node_geo(node_id))
        return geojson.FeatureCollection(features)

    def write_geojson(self, name):
        with open(name+osm_geojson_file_extension,'w') as f:
            geojson.dump(self.__geo_interface__,f,indent=2)
        
    # segments split at junctions
    # all attributes (keys) copied unless props/node_props specified.
    def create_path_network(self, name=None, seg_props=None, jct_props=None):
        if not name: name='osm'
        nwk = pnwk.PNwk(name=name)
        num_segs=0

        def add_node_tags(nwk, node_id, point, jct_props):
            node = self.nodes[node_id]
            tags = {'node_id': node_id}
            if not jct_props:
                tags.update(node.tags)
            else:
                for prop in jct_props:
                    if prop in node.tags: 
                        tags[prop] = node.tags[prop]

            nwk.add_jct(node_id, point, tags=tags)

        # process in sorted order, so that result is the same from run to run, despite multi-core processing
        way_ids = self.ways.keys()
        way_ids.sort()
        #print 'DEB way_ids:', way_ids
	for way_id in way_ids:
                way = self.ways[way_id]
		snode_id = way.node_ids[0]
                names = []
                if way.tags.has_key('name'): names.append(way.tags['name'])
                if way.tags.has_key('alt_name'): names.append(way.tags['alt_name'])
                if way.tags.has_key('loc_name'): names.append(way.tags['loc_name'])
                if way.tags.has_key('old_name'): names.append(way.tags['old_name'])
                if way.tags.has_key('official_name'): names.append(way.tags['official_name'])
                if way.tags.has_key('ref'): names += way.tags['ref'].split(';')

		points = []
                num = len(way.node_ids)
		last = num-1
		for i in xrange(num):
			node_id = way.node_ids[i]
			node = self.nodes[node_id]
			assert len(node.way_ids)>0
			points.append(node.coords)
			if len(points)<2 or (i!=last and len(node.way_ids)<2): continue
                        
                        #tags
                        tags = {'way_id':way_id}
                        if not seg_props:
                            tags.update(way.tags)
                        else:
                            for prop in seg_props:
                                if prop in way.tags: 
                                    tags[prop] = way.tags[prop]

                        num_segs += 1  # segment number used as id
                        nwk.add_seg(num_segs, snode_id, node_id, points, names=names, tags=tags)
                        add_node_tags(nwk, snode_id, points[0], jct_props)
                        add_node_tags(nwk, node_id, points[-1], jct_props)

                        snode_id = node_id;
                        points = [node.coords]
        print 'segments added:', num_segs
        return nwk

def test():
    # TODO: more rigorous testing.
    print "osm PASS"

#doit
test()

