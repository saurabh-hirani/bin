#!/usr/bin/env python

"""
Usage:
    gen_nagios_cfg.py <target> [-h|--help] --hosts <hosts-file> [--chef-cfg <chef-cfg-file>] --cache <cache-file> [--ext <ext>] [--host-tmpl <host-tmpl-file>] [--hostgroup-tmpl <hostgroup-tmpl-file>] --hostgroup-pattern <pattern>... [--verbose]

Options:
    -h,--help                                      show this help text
    -H <hosts-file>, --hosts <hosts-file>          target hosts file - one host per line
    --chef-cfg <chef-cfg-file>                     yaml based chef config file [default: chef.yml]
    --cache <cache-file>                           cache for storing looked up hosts
    --ext <extension>                              add this host extension to re-search if the search fails
    --host-tmpl <host-tmpl-file>                   template file to use for host cfg [default: host.tmpl]
    --hostgroup-tmpl <hostgroup-tmpl-file>         template file to use for hostgroup cfg [default: hostgroup.tmpl]
    -p <pattern>, --hostgroup-pattern <pattern>    hostgroup the host belongs to if fqdn 
                                                   matches this pattern
    -v, --verbose                                  verbose logging
"""

import os
import sys
import json
from string import Template

from docopt import docopt

import get_chef_attrs

def patch_tmpl(tmpl_file, tmpl_vars_list):

  tmpl = Template(open(tmpl_file).read())

  output_str = ''
  for tmpl_vars in tmpl_vars_list:
    output_str += tmpl.safe_substitute(tmpl_vars)

  return output_str

def patch_host_tmpl(tmpl_file, tmpl_vars_list):
  return patch_tmpl(tmpl_file, tmpl_vars_list)

def patch_hostgroup_tmpl(tmpl_file, tmpl_vars_list):
  output_str = ''
  uniq_hostgroups = {}
  for tmpl_vars in tmpl_vars_list:
    if 'hostgroup' not in tmpl_vars:
      continue
    hostgroup = tmpl_vars['hostgroup']
    if hostgroup not in uniq_hostgroups:
      output_str +=  patch_tmpl(tmpl_file, [{'hostgroup': hostgroup}])
      uniq_hostgroups[hostgroup] = None

  return output_str

def create_tmpl_vars_list(opts):
  tmpl_vars_list = []
  for host, host_attrs in opts['--attrs'].iteritems():
    if 'fqdn' not in host_attrs:
      continue
    if host_attrs['fqdn'] == 'None':
      host_attrs['fqdn'] = host

    ds = {}
    hostname = host_attrs['fqdn'].split('.')[0]
    ds['host_name'] = hostname
    ds['host_alias'] = hostname
    ds['address'] = host_attrs['ipaddress']

    target_hostgroup = None
    for hostgroup, pattern in opts['--hostgroup-pattern'].iteritems():
      if pattern in hostname:
        ds['hostgroup'] = hostgroup
        break

    if 'hostgroup' not in ds:
      sys.stderr.write('%s: no hostgroup\n' % ds['host_name'])
      sys.stdout.flush()

    tmpl_vars_list.append(ds)

  return tmpl_vars_list

def validate_input(opts):
  # validate only the options for this prog - leave out the options sent to
  # get_chef_attrs

  if not os.path.exists(opts['--host-tmpl']):
    print 'ERROR: Template file %s does not exist' % opts['--host-tmpl']
    sys.exit(1)

  if not os.path.exists(opts['--hostgroup-tmpl']):
    print 'ERROR: Template file %s does not exist' % opts['--hostgroup-tmpl']
    sys.exit(1)

  if opts['<target>'] != 'host' and opts['<target>'] != 'hostgroup':
    print 'ERROR: Invalid target %s - give host or hostgroup' % opts['<target>']
    sys.exit(1)

  hostgroup_patterns_map = {}
  for hostgroup_pattern in opts['--hostgroup-pattern']:
    hostgroup, pattern = hostgroup_pattern.split(':')
    hostgroup_patterns_map[hostgroup] = pattern

  opts['--hostgroup-pattern'] = hostgroup_patterns_map

def load_args(args):
  parsed_docopt = docopt(__doc__)
  return parsed_docopt

def main(opts):
  validate_input(opts)
  opts['--attrs'] = get_chef_attrs.main({
    '--hosts': opts['--hosts'],
    '--chef-cfg': opts['--chef-cfg'],
    '--cache': opts['--cache'],
    '--ext': opts['--ext'],
    '--attrs': ['ipaddress', 'fqdn'],
  })
  tmpl_vars_list = create_tmpl_vars_list(opts)

  if opts['<target>'] == 'host':
    print patch_host_tmpl(opts['--host-tmpl'], tmpl_vars_list)
  elif opts['<target>'] == 'hostgroup':
    print patch_hostgroup_tmpl(opts['--hostgroup-tmpl'], tmpl_vars_list)

if __name__ == '__main__':
  opts = load_args(sys.argv[1:])
  main(opts)
