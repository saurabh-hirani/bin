#!/usr/bin/env python

import os
import time
import argparse
import sys
import logging
import arrow
import json
import pytz
from datetime import datetime
from urllib.parse import quote as urlquote
import requests
import curlify

# TODO
# 1. Add --split to slice --start and --end time diff in different slices.

# Sample usage
# Run query from "10 minutes ago" to now
# python prometheus-run-queries.py -u http://prometheus-url -q /var/tmp/queries.txt -l '10 minutes ago'

# Run query from specific time range - between now-10m and now-11m
# python prometheus-run-queries.py -u http://prometheus-url -q /var/tmp/queries.txt \
#                                  -s $(date +%s -d "10 minutes ago") -e $(date +%s -d "11 minutes ago")

# Run query from "start_time - 10 minutes ago" to start_time
# python prometheus-run-queries.py -u http://prometheus-url -q /var/tmp/queries.txt \
#                                  -s $(date +%s -d "10 minutes ago") -l '20 minutes ago'

# Precedence
# 1. If only --lookback specified, use that.
# 2. If --lookback and --start specified, use that.
# 3. If --start and --end specified, use that.
# 4. If --start, --end and --lookback specified, throw error.


def load_args():
    """Parse cli"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", "-u", help="URL to query", required=True)
    parser.add_argument("--query-file", "-f", help="File containg queries to run", required=True)
    parser.add_argument("--lookback", "-l", help="Lookback seconds for metrics url query", default=-1)
    parser.add_argument(
        "--start",
        "-s",
        help="start timestamp for metrics query - have to specify with --end. Cannot use with --lookback",
        default=-1,
    )
    parser.add_argument(
        "--end",
        "-e",
        help="end timestamp for metrics query - have to specify with --start. Cannot use with --lookback",
        default=-1,
    )
    parser.add_argument("--url-headers", help="URL headers json str", required=False, default="{}")
    parser.add_argument("--url-args", help="URL args json str", required=False, default="{}")
    parser.add_argument("--query-step", help="Query step", default=60, required=False)
    parser.add_argument("--debug", action="store_true", dest="debug_run", help="debug run")
    parser.add_argument("--no-debug", action="store_false", dest="debug_run", help="no debug run")
    parser.set_defaults(debug_run=False)

    args = vars(parser.parse_args(sys.argv[1:]))

    args["start"] = int(args["start"])
    args["end"] = int(args["end"])
    args["url_headers"] = json.loads(args["url_headers"])
    args["url_args"] = json.loads(args["url_args"])

    return args


def validate_args(args):
    """Validate input args"""
    if args["lookback"] != -1 and args["start"] != -1 and args["end"] != -1:
        logging.error("Cannot specify --lookback, --start, --end together.")
        return False

    if not os.path.exists(args["query_file"]):
        logging.error("Query file %s does not exist", args["query_file"])
        return False

    return True


def update_args(args):
    """Update args after interpreting input"""
    lookback_seconds = 0
    if args["lookback"] != -1:
        now_obj = arrow.now()
        lookback_seconds = (now_obj - now_obj.dehumanize(args["lookback"])).total_seconds()
        if args["start"] == -1:
            args["end"] = int(time.time())
        else:
            args["end"] = args["start"]
        args["start"] = args["end"] - lookback_seconds

    with open(args["query_file"], "r") as fd:
        args["queries"] = [x.strip() for x in fd.readlines() if "#" not in x]

    args["start_fmt_local"] = datetime.fromtimestamp(args["start"]).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    args["end_fmt_local"] = datetime.fromtimestamp(args["end"]).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    logging.info("query: start local: %s", args["start_fmt_local"])
    logging.info("query: end   local: %s", args["end_fmt_local"])

    args["start_fmt"] = datetime.fromtimestamp(args["start"], tz=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    args["end_fmt"] = datetime.fromtimestamp(args["end"], tz=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    logging.info("query: start utc: %s", args["start_fmt"])
    logging.info("query: end   utc: %s", args["end_fmt"])

    return True


def query_url(args):
    """Run each query"""
    for query_str in args["queries"]:
        sys.stderr.flush()
        # query_str = urlquote(query_str)
        url = f"{args['url']}/api/v1/query_range"
        params = {
            "query": query_str,
            "start": args["start_fmt"],
            "end": args["end_fmt"],
            "step": args["query_step"],
        }
        params.update(args["url_args"])
        headers = {}
        query_output = {
            "query": query_str,
            "response": None,
        }
        headers.update(args["url_headers"])
        response = requests.get(url, params=params, headers=headers)
        logging.info(curlify.to_curl(response.request))
        if response.status_code != 200:
            query_output["response"] = response.text
            logging.error(
                "Failed to query query_str=[%s] status_code=%s response_text=%s",
                query_str,
                response.status_code,
                response.text,
            )
        query_output["response"] = response.json()
        print(json.dumps(query_output, indent=2))


def main():
    """Main function"""
    args = load_args()
    if not validate_args(args):
        return 1
    update_args(args)
    query_url(args)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    exit_status = main()
    logging.info("END")
    sys.exit(exit_status)
