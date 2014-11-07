#spiderOSM package init

import json
import os.path

import crashhandling
import log

package_dir = os.path.dirname(__file__)

# get package info from SPIDEROSM.json
with open(os.path.join(package_dir, 'SPIDEROSM_INFO.json')) as fp:
    spiderosm_info = json.load(fp)
AUTHOR = spiderosm_info['author']
AUTHOR_EMAIL = spiderosm_info['author_email']
LICENSE = spiderosm_info['license']
HOMEPAGE = spiderosm_info['homepage']

__version__ = spiderosm_info['version']

# configure logging
log.config(version=__version__)

# setup crash handling
crashhandling.init()

log.info("Initialized.")

