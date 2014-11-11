#spiderOSM package init

import json
import os.path

import config
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

log.config(version=__version__)
crashhandling.init()
log.info(config.settings)

