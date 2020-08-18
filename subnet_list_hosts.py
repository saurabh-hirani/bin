#!/usr/bin/env python

import sys
import json
import ipaddress

for host in ipaddress.ip_network(sys.argv[1]).hosts():
    print(host)

