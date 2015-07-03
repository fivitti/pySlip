#####
# Initialize the pySlip package
#####

import os
import sys

__version__ = '3.0'

from pyslip import *

try:
    from . import log as xlog
#    log = xlog.Log('pyslip.log', xlog.Log.DEBUG)
except ImportError as e:
    # if we don't have log.py, don't crash
    # fake all log(), log.debug(), ... calls
    def logit(*args, **kwargs):
        pass
    log = logit
    log.debug = logit
    log.info = logit
    log.warn = logit
    log.error = logit
    log.critical = logit


## add built-in tilesets to sys.path
#DefaultTilesets = 'tilesets'
#CurrentPath = os.path.dirname(os.path.abspath(__file__))
#
#sys.path.append(os.path.join(CurrentPath, DefaultTilesets))
