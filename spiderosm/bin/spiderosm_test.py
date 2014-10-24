#!/usr/bin/env python
'''
Check that spiderosm is installed and functioning properly.
'''

import spiderosm.test
import spiderosm.config

#doit
assert __name__ == "__main__"
#get test data dir
spiderosm.config.read_config_files()

#run tests
spiderosm.test.run_tests()

#we only get here if all the tests pass.
print 'Congratulations!  SpiderOSM appears to be properly installed and functioning.'


