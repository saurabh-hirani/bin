#!/usr/bin/env python

import sys
import base64

base64_payload = sys.stdin.read()
print(base64.b64decode(base64_payload))

