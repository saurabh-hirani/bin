#!/usr/bin/env python

# use with pyfunc
# e.g. pyfunc -f ~/github/bin/utils.py -m lookup_json -a name_to_age.json saurabh

import sys
import json

def lookup_json(filepath, key):
  lookup_ds = json.loads(open(filepath).read())
  try:
    return lookup_ds[key]
  except KeyError:
    return None
