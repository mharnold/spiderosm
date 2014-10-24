'''
Testing
'''

import config
import importlib

core_modules = (
        'bins',
        'cannames',
        'centerline',
        'colspecs',
        'config',
        'csvif',
        'dbinterface',
        'geo',
        'geofeatures',
        'match',
        'misc',
        'osm',
        'pnwk',
        'pnwk_match',
        'pnwk_matchjcts',
        'pnwk_matchspokes',
        'pnwk_namespace',
        'pnwk_network',
        'pnwk_score',
        'shp2geojson',
        )

optional_modules = (
        'postgis',
        'spatialite'
        )

def test_module(name):
    if __package__:  name = __package__ + '.' + name
    print 'testing module %s...' % name
    mod = importlib.import_module(name)
    mod.test()

def test_core_modules():
    for name in core_modules:
        test_module(name)

def test_optional_modules():
    for name in optional_modules:
        if config.settings.get(name+'_enabled'): test_module(name)

def test_modules():
    test_core_modules()
    test_optional_modules()

def run_tests():
    test_modules()

#doit
if __name__ == "__main__":
    config.read_config_files()
    run_tests()
    print 'Congratulations, spiderOSM passed all test.'
