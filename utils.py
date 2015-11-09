#!/usr/bin/env python

import sys
import json

def lookup_json(filepath, key):
  lookup_ds = json.loads(open(filepath).read())
  try:
    return lookup_ds[key]
  except KeyError:
    return None
