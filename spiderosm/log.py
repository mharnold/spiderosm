''' logging wrapper '''

import sys

import logging
from logging import debug,info,warning,error,critical

spiderosm_version=''

def reset():
    logging.root.handlers = []

def config(version=None, filename=None, level=None, force=True):
    global spiderosm_version

    if version: 
        spiderosm_version = version
    else:
        version = spiderosm_version

    if not level: level = logging.INFO

    format = '=== %%(levelname)s ===   %%(asctime)s, spiderosm %(version)s, %%(module)s:\n  %%(message)s' % {'version':version}

    if force: reset()

    logging.basicConfig(
        version=version,
        level=level,
        filename=filename,
        format=format,
        datefmt='%Y-%m-%d %H:%M:%S'
        )

def test():
    print 'log PASS'

if __name__ == "__main__":
    debug('yup')
    info('cruising altitude 30k ft')
    warning('Watch out!')
    error("I can't do that Dave.")
    critical("Crashing.  Sorry. :(")
    print 'not really.'


    config(version='test.0.0')
    info('msg after config')

    config(level=logging.DEBUG,filename='test.log.txt')
    debug('hi!')

