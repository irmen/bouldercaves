#!/bin/sh
find . -name '*.pyc' -exec rm {} \;
find . -name __pycache__ -exec rm -r {} \;
python3 -m zipapp --python '/usr/bin/env python3' --output bouldercaves.pyz zipapp
zip -ur9 bouldercaves.pyz bouldercaves
