''' log system info before exiting due to uncaught exception '''

import os
import sys

import config
import log

orig_excepthook = None

# log system info before exiting due to uncaught exception.
def crash_info_excepthook(exctype, value, traceback):
    log.critical("""
  --- config.info: 
%s

  --- config.settings:
%s
  """, config.info, config.settings)

    orig_excepthook(exctype, value, traceback)

# chain in our excepthook
def init():
    global orig_excepthook
    orig_excepthook = sys.excepthook
    sys.excepthook = crash_info_excepthook

