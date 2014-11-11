''' 
spiderosm config settings
'''

import json
import os
import sys

info = {}
settings = {}

# location of spiderosm package dir
# assume current directory if 'spiderosm' module not loaded
try:
    import spiderosm
    settings['spiderosm_dir'] = spiderosm.__path__[0]
except ImportError:
    settings['spiderosm_dir'] = os.getcwd()

def get_info():
    package_dir = os.path.dirname(__file__)
    info['package_dir'] = package_dir

    # get package info from SPIDEROSM.json
    with open(os.path.join(package_dir, 'SPIDEROSM_INFO.json')) as fp:
        info.update(json.load(fp))

    # add platform info etc
    info['sys.version'] = sys.version
    info['sys.platform'] = sys.platform
    info['os.name'] = os.name

def default_settings():
    # data for spiderosm tests
    settings['spiderosm_test_data_dir'] = os.path.join(settings['spiderosm_dir'],'test_data')

    # enabling postgis or spatialite causes results to be written to these database by toplevels 
    # such as examples/match_berkeley.py and examples/match_portland.py.  
    # examples/test_spiderosm also will test enabled database interfaces
    settings['postgis_enabled'] = False
    settings['spatialite_enabled'] = False

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

#on load
get_info()
default_settings()
read_config_files()

