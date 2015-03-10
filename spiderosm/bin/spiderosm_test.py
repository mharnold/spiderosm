#!/usr/bin/env python
'''
Check that spiderosm is installed and functioning properly.
'''

import spiderosm.config
import spiderosm.log
import spiderosm.test

def dump_config():
    spiderosm.log.info('config.info: %s', spiderosm.config.info_str())
    spiderosm.log.info('config.settings: %s', spiderosm.config.settings_str())
    

#doit
assert __name__ == "__main__"

dump_config()
spiderosm.test.run_tests()
dump_config()

#we only get here if all the tests pass.
spiderosm.log.info('Congratulations!  SpiderOSM appears to be properly installed and functioning.')


