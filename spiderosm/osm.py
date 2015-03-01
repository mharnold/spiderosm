import gzip
import json
import os
import sys

import geojson
import pyproj

import geo
import geofeatures
import log
import misc
import osmparser
import pnwk

OSM_GEOJSON_FILE_EXTENSION = '.osm.geojson'
OSM_JSON_FILE_EXTENSION = '.osm.json'

def _overpass_get(query):
    url = 'http://overpass-api.de/api/interpreter'
    parms = {'data':query}
    response_headers = {}
    data = misc.get_url(url,parms=parms,gzip=True,info=response_headers)
    #print 'DEB _overpass_get response_headers:',response_headers
    return data

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

    # imposm.parser callback for coords (called for ALL nodes, both those with and without tags.)
    def _parse_coords(self, coords_in):
        for osmId, lon, lat in coords_in:
	    if not (osmId in self.nodes): self._parse_node(osmId, (lon,lat))

    # callback for nodes (with tags only, in case of imposm.parser)
    def _parse_nodes(self, nodes_in):
	for osmId,tags,coords in nodes_in:
            self._parse_node(osmId, coords, tags=tags)

    def _parse_way(self, osmid, tags, refs):
	    # roads only
	    if not ('highway' in tags): return
            
            # at least two nodes (in clip area)
            if self.clip_rect:
                count = 0
                for ref in refs:
                    if ref in self.nodes: 
                        count += 1
                        if count >= 2: break
                if count < 2: return

            # remove refs to missing nodes
            new = []
            for ref in refs:
                if ref in self.nodes: new.append(ref)
            refs = new

	    self.ways[osmid] = Way(tags=tags, node_ids=refs)	

    # callback for ways 
    def _parse_ways(self, ways_in):
        for osmid, tags, refs in ways_in:
            self._parse_way(osmid, tags, refs)

    # initialize from osm json data (acquired, e.g., from overpass api)
    def _parse_osm_json(self, osm_json):
        log.info('Parsing osm json data')
        # nodes
        for element in osm_json["elements"]:
            if element["type"] == "node": 
                osmId = element["id"]
                coords = (element["lon"], element["lat"])
                tags = {}
                if len(element)>4:
                    for (k,v) in element.items():
                        tags[k]=v
                self._parse_node(osmId, coords, tags=tags)

        # ways
        for element in osm_json["elements"]:
            if element["type"] == "way": 
                osmId = element["id"]
                tags = element["tags"]
                refs = element["nodes"]
                self._parse_way(osmId, tags, refs)
      				
        log.info('%d ways, %d nodes', len(self.ways), len(self.nodes))

    # read in an OSM data file
    # processing in two passes to avoid thrashing when clipping an area from huge files.
    def _parse_input_file(self, file_name, xml_format=None):
        if xml_format == None:
	    xml_format = (os.path.splitext(file_name)[1] == '.xml')
				
        # first pass: nodes 
        log.info('Reading nodes from osm file: %s', file_name)
        if xml_format:
            p = osmparser.OSMParser(
                    all_nodes_callback=self._parse_nodes)
	    p.parse_xml_file(file_name)
	else:
            # osmparser.py does not currently handle .osm.pbf, attempt to use imposm.parser
            import imposm.parser
	    p = imposm.parser.OSMParser(
                    coords_callback=self._parse_coords,
                    nodes_callback=self._parse_nodes)
	    p.parse(file_name)

        # second pass: ways
        log.info('Reading ways from osm file: %s', file_name)
        if xml_format:
            p = osmparser.OSMParser(
	        ways_callback=self._parse_ways)
	    p.parse_xml_file(file_name)
        else:
	    p = imposm.parser.OSMParser(
	        ways_callback=self._parse_ways)
            p.parse(file_name)
				
        log.info('%d ways, %d nodes', len(self.ways), len(self.nodes))

    # OBSOLETE version (full area query / xml)
    # download OSM data via overpass API and parse it.
    def _import_and_parse_overpass_data_map_query(self):
        # need bbox in geo: (lon,lat)
        if self.proj:
            geo_bbox = self.proj.project_box(self.clip_rect, rev=True)
        else:
            geo_bbox = self.clip_rect
        self.clip_rect = None # no need to double clip
        
        overpass_url='http://overpass-api.de/api/map?bbox=%f,%f,%f,%f' % geo_bbox
        print 'DEB overpass url:', overpass_url
        (temp_file_name, headers) = misc.urlretrieve(overpass_url,suffix='.osm.xml',gzip=True)
        self._parse_input_file(temp_file_name, xml_format=True)
        os.remove(temp_file_name)

    # download OSM data via overpass API and parse it.
    def _import_and_parse_overpass_data(self):
        # need bbox in geo: (lon,lat)
        if self.proj:
            geo_bbox = self.proj.project_box(self.clip_rect, rev=True)
        else:
            geo_bbox = self.clip_rect
        self.clip_rect = None # no need to double clip
        
        # highway ways (only) and referenced nodes (in json format)
        template = """
            [out:json];

            // ways of type highway 
            way({min_lat}, {min_lon}, {max_lat}, {max_lon})[highway];out body qt;

            // referenced nodes 
            >; out body qt;
        """

        (min_lon, min_lat, max_lon, max_lat) = geo_bbox
        query = template.format(
                min_lat=min_lat,
                min_lon=min_lon,
                max_lat=max_lat,
                max_lon=max_lon)
        data_string = _overpass_get(query)
        #print 'DEB data_string len:', len(data_string)
        #print 'data_string:', data_string
        log.info('json string -> json, begin.')
        data_json = json.loads(data_string)
        self._parse_osm_json(data_json)
       
    # remove stutters (repeated node refs) from ways
    def _remove_stutters(self):
        num_removed = 0
        for way_id in self.ways:
            new = []
            for ref in self.ways[way_id].node_ids:
                if len(new) > 0 and ref == new[-1]:
                    log.warning('DELETING REPEATED NODE REFERENCE %d from way %d', ref, way_id)
                    num_removed += 1
                else:
                    new.append(ref)
            self.ways[way_id].node_ids = new 
        if num_removed>0: log.warning('REMOVED %d REPEATED NODE REFERENCES.', num_removed)

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

    # initialize from OSM input file, if given, else via overpass API
    def __init__(self, file_name=None, clip_rect=None, target_proj=None, srs=None):
        # if no file_name given we need to know what area to get via overpass 
        assert file_name or clip_rect
        self.clip_rect = clip_rect

        self.srs = None
        if srs:
            self.srs = srs

            if target_proj:
                assert target_proj == srs.proj4text
            else:
                target_proj = srs.proj4text
            
        self.proj=None
        if target_proj: self.proj = geo.Projection(target_proj)

        if file_name:
	    self._parse_input_file(file_name)
        else:
            #self._import_and_parse_overpass_data_map_query()
            self._import_and_parse_overpass_data()
            
        #remove stutters from ways (repeated node refs)
        self._remove_stutters()

        # remove any ways with less than two nodes left.
        self._remove_malformed_ways()

	# add way references to nodes
	self._add_refs_to_nodes()

	# remove nodes that have neither tags nor are referenced by ways
	self._vacuum_nodes()

	# count intersections
	numi = 0
	for id,node in self.nodes.items():
	    if len(node.way_ids)>1: numi += 1
	log.info('%d nodes after cleanup, %d intersections.', len(self.nodes), numi)

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
        return geofeatures.geo_feature_collection(features, srs=self.srs)

    def write_geojson(self, name):
        geofeatures.write_geojson(self,name+OSM_GEOJSON_FILE_EXTENSION)
        
    # segments split at junctions
    # all attributes (keys) copied unless seg_props/jct_props specified.
    def create_path_network(self, name=None, seg_props=None, jct_props=None):
        if not name: name='osm'
        nwk = pnwk.PNwk(name=name, srs=self.srs)
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
        log.info('%d segments added to OSM PNwk.', num_segs)
        return nwk

def test():
    # tiny OSM area in Berkeley Marina
    clip_rect=(-122.31851,37.86517,-122.31635,37.86687)
    osm_data = OSMData(clip_rect=clip_rect)

    def feature_func(feature,props):
        if props.get('name') != 'Seawall Drive': return False
        return True

    found = geofeatures.filter_features(osm_data,
            feature_func=feature_func,
            geom_type='LineString')
    assert len(found) > 0

    print "osm PASS"

#doit
if __name__ == '__main__':
    test()

