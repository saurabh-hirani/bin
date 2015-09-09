#!/usr/bin/env python

"""
Usage:
    gen-nagios-cfg (host) [-h|--help] --hosts <hosts-file> --chef-cfg <chef-cfg-file> --cache <cache-file> --tmpl <tmpl-file>

Options:
    -h,--help                             show this help text
    -H <hosts-file>, --hosts <hosts-file> target hosts file - one host per line
    --chef-cfg <chef-cfg-file>            yaml based chef config file
    --cache <cache-file>                  cache for storing looked up hosts
    --attrs <attr>                        chef attributes to search
    --tmpl <tmpl-file>                    template file to use for host cfg
"""

from docopt import docopt
import get_chef_attrs

def validate_input(opts):
  if not os.path.exists(opts['--tmpl']):
    print 'ERROR: Template file %s does not exist' % opts['--tmpl']
    sys.exit(1)
  # rest to be validated by get_chef_attrs

def load_args(args):
  parsed_docopt = docopt(__doc__)
  return parsed_docopt

def main(args):
  opts = load_args(args)
  attrs = get_chef_attrs.main({
    '--host': opts['--hosts'],
    '--chef-cfg': opts['--chef-cfg'],
    '--cache': opts['--cache'],
  })
  print json.dumps(attrs, indent=4)

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
