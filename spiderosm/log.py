''' logging wrapper '''

import logging
from logging import debug,info,warning,error,critical

def config(version=""):

    format = '=== %%(asctime)s, spiderosm %(version)s, %%(module)s, %%(levelname)s:\n  %%(message)s' % {'version':version}

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        datefmt='%Y-%m-%d %H:%M:%S'
        )

def test():
    print 'log PASS'

if __name__ == "__main__":
    config(version='?.?.?')
    
    debug('yup')
    info('cruising altitude 30k ft')
    warning('Watch out!')
    error("I can't do that Dave.")
    critical("Crashing.  Sorry. :(")
