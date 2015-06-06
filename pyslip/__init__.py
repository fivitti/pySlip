#####
# Initialize the pySlip package
#####

import os
import sys

# add built-in tilesets to sys.path
print('########## __init__.py ##########')
DefaultTilesets = 'tilesets'
CurrentPath = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(CurrentPath, DefaultTilesets))
