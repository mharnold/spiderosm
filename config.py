''' 
spiderosm config settings
'''

import os
import json

settings = {}

def read_config_files(filenames=None,paths=None):
    if not filenames: filenames = ('.spiderosm.json', 'config.spiderosm.json')
    if not paths: paths = ('~', '.')

    for path in paths:
        path = os.path.expanduser(path)
        for fn in filenames:
            fullpath = os.path.join(path,fn)
            if os.path.exists(fullpath):
                print 'Reading %s' % fullpath
                with open(fullpath, 'r') as f:
                    new = json.load(f)
                    settings.update(new)

def test():
    fns = ( '.spiderosm.json', 'config.spiderosm.json' )
    paths = ( '~','.' )
    #read_config_files(fns,paths)
    #print 'settings', settings
    print 'config test PASS.'

#doit
test()



