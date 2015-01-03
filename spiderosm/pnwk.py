'''
Path Network.
Built up via class extension:
    PNwkNamespace  - network name, attribute name prefixes (BASE CLASS)
    PNwkNetwork    - path network implementation, read, write
    PNwkScore      - match scoring
    PNwkMatchJcts
    PNwkMatchSpokes
    PNwkMatch      - matcher
    PNwk           - top level.
'''

import pnwk_match

class PNwk(pnwk_match.PNwkMatch):
    pass

def test():
    foo = PNwk('foo')
    assert foo.name == 'foo'

    print 'pnwk PASS'

#doit
if __name__ == "__main__":
    test()
