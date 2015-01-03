'''
Base class for PNwk (Path Network)
'''

class PNwkNamespace(object):

    NAMESPACE_SEP = '$'

    def __init__(self,name=None):

        #network name
        if not name: name = 'nwk'
        self.name = name

        # namespace prefixes for properties
        sep = self.NAMESPACE_SEP
        self.client_name_space = self.make_namespace(name)
        self.pnwkNameSpace = self.make_namespace(name + '_pnwk') 
        self.match_namespace = self.make_namespace('match')

    def make_namespace(self,name):
        return name + self.NAMESPACE_SEP

    def add_namespace(self, props, nameSpace):
        if not props: return {}
        out = {}
        for key in props.keys():
            out[nameSpace+key] = props[key]
        return out

    def split_off_namespace(self,name):
        i = name.find(self.NAMESPACE_SEP)+1
        return (name[:i],name[i:])

def test_add_namespace(nsp):
    a = {'id':1, 'name':2, 'length':3}
    ns = nsp.make_namespace('oz')
    b = nsp.add_namespace(a, ns)
    assert b['oz' + nsp.NAMESPACE_SEP + 'name'] == 2

def test_split_off_namespace(nsp):
    (ns,base) = nsp.split_off_namespace('foo$bar')
    assert ns == 'foo$'
    assert base == 'bar'
    (ns,base) = nsp.split_off_namespace('bar')
    assert ns == ''
    assert base == 'bar'
    (ns,base) = nsp.split_off_namespace('foo$bar$zar')
    assert ns == 'foo$'
    assert base == 'bar$zar'

def test():
    nsp = PNwkNamespace(name='fish')
    test_add_namespace(nsp)
    test_split_off_namespace(nsp)
    print 'pnwk_namespace PASS'

#doit
if __name__ == "__main__":
    test()
