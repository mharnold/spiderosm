''' 
spiderosm config settings
'''

import json
import os
import sys

import log

info = {}
settings = {}

def _get_info():
    package_dir = os.path.dirname(__file__)
    info['package_dir'] = package_dir

    # get package info from SPIDEROSM.json
    with open(os.path.join(package_dir, 'SPIDEROSM_INFO.json')) as fp:
        info.update(json.load(fp))

    # add platform info etc
    info['sys.version'] = sys.version
    info['sys.platform'] = sys.platform
    info['os.name'] = os.name

def _default_settings():
    # data for spiderosm tests
    settings['spiderosm_test_data_dir'] = os.path.join(info['package_dir'],'test_data')

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
                log.info('Reading %s', fullpath)
                with open(fullpath, 'r') as f:
                    new = json.load(f)
                    settings.update(new)

def info_str():
    info_str=''
    for key in sorted(info.keys()):
        info_str += "\n    %s: %s" % (key,info[key])
    return info_str

def settings_str():
    settings_str=''
    for key in sorted(settings.keys()):
        settings_str += "\n    %s: %s" % (key,settings[key])
    return settings_str

def log_settings():
    log.info('config.info:%s', info_str())
    log.info('config.settings:%s', settings_str())

def test():
    fns = ( '.spiderosm.json', 'config.spiderosm.json' )
    paths = ( '~','.' )
    #read_config_files(fns,)
    #print 'settings', settings
    print 'config PASS'

#on load
_get_info()
log.config(version=info['version'])
_default_settings()
read_config_files()

