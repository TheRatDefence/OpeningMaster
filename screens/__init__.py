"""
The individual screens displayed by the app.

Screens in this package are automatically loaded into the MainDisplay if:

1. They implement the Screen interface

2. Registered through the @Screen.register('name') decorator
"""

# ------------| Automatic Screen Import |------------ #

import os
import importlib

# TODO(): Implement logging loading messages for each screen

print("Importing screens...")

# Get all screen files in this directory
screens_dir = str(os.path.dirname(__file__))
screens = os.listdir(screens_dir)

screens.remove('__init__.py')
if '__pycache__' in screens:
    screens.remove('__pycache__')

for screen in screens:
    screen = str(screen).removesuffix('.py')
    importlib.import_module('screens.' + screen)