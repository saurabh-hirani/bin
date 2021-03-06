#!/usr/bin/env python
"""
Usage:
    get_chef_attrs.py [-h|--help] --hosts <hosts-file> [--chef-cfg <chef-cfg-file>] --cache <cache-file> [--ext <extension>] --attrs <attr>... [--verbose] 

Options:
    -h,--help                             show this help text
    -H <hosts-file>, --hosts <hosts-file> target hosts file - one host per line
    --chef-cfg <chef-cfg-file>            yaml based chef config file [default: chef.yml]
    --cache <cache-file>                  cache for storing looked up hosts
    --attrs <attr>                        chef attributes to search
    --ext <extension>                     add this host extension to re-search if the search fails
    -v, --verbose                         verbose mode
"""

import os
import sys
import yaml
import json

from docopt import docopt
import chef

def lookup_chef(opts, hosts):
  chef_cfg = yaml.load(open(opts['--chef-cfg']).read())
  cache = {}

  with chef.ChefAPI(chef_cfg['chef']['host'], chef_cfg['chef']['pem'],
                    chef_cfg['chef']['user']):

    for host in hosts:
      attrs_map = {}

      orig_host = host
      if '@' in host:
        _, host = host.split('@')

      n = chef.Node(host)
      ipaddr =  n.attributes.get('ipaddress')

      if ipaddr is None or ipaddr == 'None':
        if opts['--ext'] is not None:
          host = host + '.' + opts['--ext']
          n = chef.Node(host)
          ipaddr =  n.attributes.get('ipaddress')

      for attr in opts['--attrs']:
        attrs_map[str(attr)] = str(n.attributes.get(attr))

      if ipaddr:
        cache[host] = attrs_map
      else:
        cache[host] = {}

      if '--verbose' in opts and opts['--verbose']:
        print "------------"
        print host
        print json.dumps(attrs_map, indent=4)

  return cache

def get_chef_attrs(opts):

  hosts = []
  with open(opts['--hosts']) as f:
    hosts = [x.strip() for x in f.readlines()]

  unresolved_hosts = []

  cache = json.loads(open(opts['--cache']).read())

  for host in hosts:
    _, host = host.split('@')
    host_variants = []

    host_variants.append(host)
    host_variants.append(host.split('.')[0])

    found = False

    for host_variant in host_variants:
      if host_variant in cache:
        found = True
        break

    if not found:
      unresolved_hosts.append(host)

  if unresolved_hosts:
    hosts_info = lookup_chef(opts, unresolved_hosts)
    for host in hosts_info:
      cache[host] = hosts_info[host]
    with open(opts['--cache'], 'w') as f:
      f.write(json.dumps(cache, indent=4))

  return cache

def validate_input(opts):
  if not os.path.exists(opts['--hosts']):
    print 'ERROR: hosts file %s does not exist' % opts['--hosts']
    sys.exit(1)

  if not os.path.exists(opts['--chef-cfg']):
    print 'ERROR: chef cfg file %s does not exist' % opts['--chef-cfg']
    sys.exit(1)

  if not opts['--attrs']:
    print 'ERROR: Empty attrs' % opts['--attrs']
    sys.exit(1)

  if not os.path.exists(opts['--cache']):
    with open(opts['--cache'], 'w') as f:
      f.write('{}')

def load_args(args):
  parsed_docopt = docopt(__doc__)
  return parsed_docopt

def main(opts):
  validate_input(opts)
  return get_chef_attrs(opts)

if __name__ == '__main__':
  opts = load_args(sys.argv[1:])
  attrs = main(opts)
  print json.dumps(attrs, indent=4)
