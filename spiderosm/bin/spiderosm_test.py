#!/usr/bin/env python
'''
Check that spiderosm is installed and functioning properly.
'''

import spiderosm.config
import spiderosm.log
import spiderosm.test

#doit
assert __name__ == "__main__"
#get test data dir
spiderosm.config.read_config_files()

#run tests
spiderosm.test.run_tests()

#we only get here if all the tests pass.
spiderosm.log.info('Congratulations!  SpiderOSM appears to be properly installed and functioning.')


