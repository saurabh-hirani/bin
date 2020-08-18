#!/usr/bin/env python

import sys
import json
import ipaddress

network_1_str = sys.argv[1]
network_2_str = sys.argv[2]

network_1 = ipaddress.ip_network(network_1_str)
network_2 = ipaddress.ip_network(network_2_str)

if network_1.subnet_of(network_2):
    print(True)
    sys.exit(0)

network_1_hosts = [str(x) for x in ipaddress.ip_network(network_1).hosts()]
network_2_hosts = [str(x) for x in ipaddress.ip_network(network_2).hosts()]

diff_hosts = set(network_1_hosts).difference(network_2_hosts)

print(
    json.dumps({
        network_1_str + '-hosts': network_1_hosts,
        network_2_str + '-hosts': network_2_hosts,
        'diff_hosts': list(sorted(ipaddress.ip_address(host) for host in diff_hosts))
    }, indent=2, default=str)
)

sys.exit(1)
