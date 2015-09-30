#!/usr/bin/env python

# Advanced docopt examples

"""
Usage:
  test_docopt.py test1 [(--warning <warning> --critical <critical>)]
  test_docopt.py test2 (--host <host> --port <port> --uri <uri> [--nports <nports>] | --url <url>)
  test_docopt.py test3 [(--callback_path <cbpath> --callback_func <cbfunc> | --callback_module <cbmod> --callback_func <cbfunc>)]

Options:
  # test1 - either specificy both warning and critical or none
  --warning <warning>
  --critical <critical>

  # test2 - either specifiy ((host, port, uri) and optionally nports) or speicify (url)
  --host <host>
  --port <port>
  --uri  <uri>
  --nports <nports>
  --url <url>

  # test3 - either specify callback_path or specify callback_module - but when either specified - specify callback_func
  --callback_path <cbpath>
  --callback_module <cbmod>
  --callback_func <cbfunc>
"""

import sys

from docopt import docopt
from schema import Schema, And, Use, SchemaError

def load_args():
  parsed_docopt = docopt(__doc__)
  return parsed_docopt

def load_schema():
  return {
    'test1': Schema({
              '--warning': And(Use(int), lambda n: 1 <= n <= 99,
                               error='Invalid warning val - 1 <= warning <= 99'),
              '--critical': And(Use(int), lambda n: 1 <= n <= 99,
                                error='Invalid critical val - 1 <= critical <= 99')
            })
  }

def validate_opts(opts):
  if opts['test1'] is True:
    cmd_schema = load_schema()['test1']
    data = {
      '--warning': opts['--warning'],
      '--critical': opts['--critical'],
    }
    try:
      validated = cmd_schema.validate(data)
    except SchemaError as e:
      sys.exit(e.code)

if __name__ == '__main__':
  opts = load_args()
  opts_schema = load_schema()
  validate_opts(opts)
