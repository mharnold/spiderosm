#spiderOSM package init

import json
import os.path

import config
import crashhandling
import log

__version__ = config.info['version']
AUTHOR = config.info['author']
AUTHOR_EMAIL = config.info['author_email']
LICENSE = config.info['license']
HOMEPAGE = config.info['homepage']

crashhandling.init()
config.log_settings()
