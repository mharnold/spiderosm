'''
Integration Testing
'''

import config
import match

def tests():
    match.tests()
    print 'test PASS'

#doit
if __name__ == "__main__":
    config.read_config_files()
    tests()
