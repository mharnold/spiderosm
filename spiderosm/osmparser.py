import StringIO
import sys
import xml.sax 

class OSMParser(object):

    # relations currently ignored
    def __init__(self, all_nodes_callback=None,ways_callback=None):
        self._all_nodes_callback = all_nodes_callback
        self._ways_callback = ways_callback

    def parse_xml_file(self,filename_or_stream):
        parser = xml.sax.make_parser()
        parser.setContentHandler(self._ContentHandler(
            all_nodes_callback=self._all_nodes_callback,
            ways_callback=self._ways_callback))
        parser.parse(filename_or_stream)

    class _ContentHandler(xml.sax.handler.ContentHandler):
        MAX_LIST_LENGTH = 10000

        # get ready for next node or way
        def reset(self):
            # set to node or way when in the middle of processing one.
            self.current_type = None
            self.id = None
            self.tags = {}

        def __init__(self, all_nodes_callback=None, ways_callback=None):
            self.all_nodes_callback = all_nodes_callback
            self.ways_callback = ways_callback
            self.nodes = []
            self.ways = []
            self.reset()

        def startElement(self, name, attrs):
            #print 'DEB start element:', name, attrs
            if name == 'node' and self.all_nodes_callback:
                assert not self.current_type
                self.current_type = name
                self.id = int(attrs['id'])
                self.coords = map(float, (attrs['lon'], attrs['lat']))
            elif name == 'way' and self.ways_callback:
                assert not self.current_type
                self.current_type = name
                self.id = int(attrs['id'])
                self.refs = []
            elif name == 'tag':
                if self.current_type: 
                    self.tags[attrs['k']] = attrs['v']
            elif name == 'nd':
                if self.current_type == 'way':
                    self.refs.append(int(attrs['ref']))

        def endElement(self, name): 
            #print 'DEB end element:', name
            if name == 'node' and self.all_nodes_callback:
                assert self.current_type == name
                self.nodes.append((self.id, self.tags, self.coords))
                if len(self.nodes) >= self.MAX_LIST_LENGTH: self._process_nodes()
                self.reset()
            elif name == 'way' and self.ways_callback:
                assert self.current_type == name
                self.ways.append((self.id, self.tags, self.refs))
                if len(self.ways) >= self.MAX_LIST_LENGTH: self._process_ways()
                self.reset()

        def endDocument(self):
            if self.all_nodes_callback: self._process_nodes()
            if self.ways_callback: self._process_ways()

        def _process_nodes(self):
            if len(self.nodes)>0: 
                self.all_nodes_callback(self.nodes)
                self.nodes = []

        def _process_ways(self):
            if len(self.ways)>0: 
                self.ways_callback(self.ways)
                self.ways = []

def test():
    test_data = '''<?xml version="1.0" encoding="UTF-8"?>
<osm fake="yes">
 <bounds minlat="37" minlon="-122.4" maxlat="38" maxlon="-122.2"/>
  <node id="1" version="3" changeset="2" uid="4444" lat="37.86" lon="-122.310">
  <tag k="leisure" v="slipway"/>
 </node>
  <node id="10" lat="37.9" lon="-122.35"/>
  <way id="1" visible="true" version="4" changeset="400" user="me" uid="99">
  <nd ref="10"/>
  <nd ref="11"/>
  <nd ref="12"/>
  <tag k="addr:city" v="Berkeley"/>
  <tag k="highway" v="unclassified"/>
  <tag k="name" v="Watery Way"/>
   </way>
</osm>'''

    node_dict = {}
    way_dict  = {}

    def all_nodes_cb(nodes):
        for node in nodes:
            node_id,tags,coords = node
            node_dict[node_id] = {'coords':coords, 'tags':tags}
    def ways_cb(ways):
        for way in ways:
            way_id,tags,node_refs = way
            way_dict[way_id] = {'node_refs':node_refs, 'tags':tags}

    p = OSMParser(all_nodes_callback=all_nodes_cb, ways_callback=ways_cb)
    test_data_stream = StringIO.StringIO(test_data)
    p.parse_xml_file(test_data_stream)
    test_data_stream.close()
    
    assert len(node_dict) == 2
    assert len(way_dict) == 1 
    assert node_dict[1]['tags']['leisure'] == 'slipway'
    refs = way_dict[1]['node_refs']
    assert len(refs) == 3 and 12 in refs
    assert way_dict[1]['tags']['addr:city'] == 'Berkeley'
    assert way_dict[1]['tags']['name'] == 'Watery Way'

    #print 'DEB nodes', node_dict
    #print 'DEB ways', way_dict

    print 'osmparser PASS'

#doit
if __name__ == "__main__":
    test()
