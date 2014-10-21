''' 
spiderosm config settings
'''

import os
import json

settings = {}

# location of spiderosm package dir
# assume current directory if 'spiderosm' module not loaded
try:
    import spiderosm
    settings['spiderosm_dir'] = spiderosm.__path__[0]
except ImportError:
    settings['spiderosm_dir'] = os.getcwd()

# data for spiderosm tests
settings['spiderosm_test_data_dir'] = os.path.join(settings['spiderosm_dir'],'test_data')

#enabling postgis or spatialite causes results to be written to these database by toplevels 
# such as examples/match_berkeley.py and examples/match_portland.py.  
# examples/test_spiderosm also will test enabled database interfaces
settings['postgis_enabled'] = False
settings['spatialite_enabled'] = False

# main programs call this explictly after setting 'default' conf values.
def read_config_files(filenames=None,paths=None,quiet=False):
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
    print 'config PASS'

#doit
test()



