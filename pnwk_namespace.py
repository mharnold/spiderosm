'''
Base class for PNwk (Path Network)
'''

class PNwkNamespace(object):

    nameSpaceSep = '$'

    def __init__(self,name=None):

        #network name
        if not name: name = 'nwk'
        self.name = name

        # namespace prefixes for properties
        sep = self.nameSpaceSep
        self.clientNameSpace = self.makeNamespace(name)
        self.pnwkNameSpace = self.makeNamespace(name + '_pnwk') 
        self.matchNameSpace = self.makeNamespace('match')

    def makeNamespace(self,name):
        return name + self.nameSpaceSep

    def addNamespace(self, props, nameSpace):
        if not props: return {}
        out = {}
        for key in props.keys():
            out[nameSpace+key] = props[key]
        return out

    def splitOffNamespace(self,name):
        i = name.find(self.nameSpaceSep)+1
        return (name[:i],name[i:])

def testAddNamespace(nsp):
    a = {'id':1, 'name':2, 'length':3}
    ns = nsp.makeNamespace('oz')
    b = nsp.addNamespace(a, ns)
    assert b['oz' + nsp.nameSpaceSep + 'name'] == 2

def testSplitOffNamespace(nsp):
    (ns,base) = nsp.splitOffNamespace('foo$bar')
    assert ns == 'foo$'
    assert base == 'bar'
    (ns,base) = nsp.splitOffNamespace('bar')
    assert ns == ''
    assert base == 'bar'
    (ns,base) = nsp.splitOffNamespace('foo$bar$zar')
    assert ns == 'foo$'
    assert base == 'bar$zar'

def test():
    nsp = PNwkNamespace(name='fish')
    testAddNamespace(nsp)
    testSplitOffNamespace(nsp)
    print 'namespace test PASSED'

#doit
test()
