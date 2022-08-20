#!/usr/bin/env python

import os
import argparse
import sys
import logging
import arrow
import json
import pytz
import datetime
from urllib.parse import quote as urlquote
import requests
import curlify

"""
Run prometheus queries from the cli.

Order of evaluation

1. If only --lookback specified => start = now - lookback, end = now

prometheus-run-queries.py -u $test_prometheus_url -f /var/tmp/queries.txt \
                          -l '10 minutes ago' 2>&1 | less

now=11:30:00
start=11:20:00
end=11:30:00

2. If --lookback and --end specified => start = end - lookback


prometheus-run-queries.py -u $test_prometheus_url -f /var/tmp/queries.txt \
                          -e $(date +%s -d "10 minutes ago") -l '20 minutes ago' 2>&1 | less

now=11:30:00
start=11:10:00
end=11:20:00

3. If --lookback and --start specified => start = start - lookback, end = now


prometheus-run-queries.py -u $test_prometheus_url -f /var/tmp/queries.txt \
                          -s $(date +%s -d "10 minutes ago") -l '20 minutes ago' 2>&1 | less

now=11:30:00
start=11:00:00
end=11:30:00


4. If only --start specified => start = start, end = now

prometheus-run-queries.py -u $test_prometheus_url -f /var/tmp/queries.txt \
                          -s $(date +%s -d "10 minutes ago") 2>&1 | less

now=11:30:00
start=11:20:00
end=11:30:00

5. If --start and --end specified => start = start, end = end

prometheus-run-queries.py -u $test_prometheus_url -f /var/tmp/queries.txt \
                          -s $(date +%s -d "11 minutes ago") -e $(date +%s -d "10 minutes ago") 2>&1 | less

now=11:30:00
start=11:19:00
end=11:20:00

6. For everything else, raise an error.
"""


def load_args():
    """Parse cli"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", "-u", help="URL to query", required=True)
    parser.add_argument("--query-file", "-f", help="File containg queries to run", required=True)
    parser.add_argument("--lookback", "-l", help="Lookback seconds for metrics url query", default=-1)
    parser.add_argument(
        "--start",
        "-s",
        help="start timestamp for metrics query - have to specify with --end",
        default=-1,
    )
    parser.add_argument(
        "--end",
        "-e",
        help="end timestamp for metrics query - have to specify with --start.",
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
    now_obj = arrow.now()
    now_obj_fmt = now_obj.datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    now_obj_timestmap = now_obj.datetime.timestamp()

    args["input_start_fmt_local"] = -1
    args["input_end_fmt_local"] = -1

    if args["start"] != -1:
        args["input_start_fmt_local"] = datetime.datetime.fromtimestamp(args["start"]).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
    if args["end"] != -1:
        args["input_end_fmt_local"] = datetime.datetime.fromtimestamp(args["end"]).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # If --start, --end, --lookback empty => error
    if args["start"] == -1 and args["end"] == -1 and args["lookback"] == -1:
        logging.error("Empty --start, --end, --lookback.")
        return False

    if args["lookback"] != -1:
        lookback_seconds = (now_obj - now_obj.dehumanize(args["lookback"])).total_seconds()

    # 1. If only --lookback specified => start = now - lookback, end = now
    if args["start"] == -1 and args["end"] == -1:
        args["start"] = now_obj_timestmap - lookback_seconds
        args["end"] = now_obj_timestmap

    # 2. If --lookback and --end specified => start = end - lookback
    if args["start"] == -1 and args["end"] != -1:
        if args["lookback"] == -1:
            logging.error(
                "Empty --start, empty --lookback, non-emtpy --end. If --start is empty --lookback should not be empty"
            )
            return False
        args["start"] = args["end"] - lookback_seconds

    # 3. If --lookback and --start specified => start = start - lookback, end = now
    # 4. If only --start specified => start = start, end = now
    if args["start"] != -1 and args["end"] == -1:
        if args["lookback"] != -1:
            args["start"] = args["start"] - lookback_seconds
        args["end"] = now_obj_timestmap

    if args["start"] > args["end"]:
        logging.error("start = %d > end = %d", args["start"], args["end"])
        return False

    with open(args["query_file"], "r") as fd:
        args["queries"] = [x.strip() for x in fd.readlines() if "#" not in x]

    args["start_fmt"] = datetime.datetime.fromtimestamp(args["start"], tz=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    args["end_fmt"] = datetime.datetime.fromtimestamp(args["end"], tz=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    args["start_fmt_local"] = datetime.datetime.fromtimestamp(args["start"]).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    args["end_fmt_local"] = datetime.datetime.fromtimestamp(args["end"]).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    delta = str(datetime.timedelta(seconds=(args["end"] - args["start"])))

    logging.info("query: now                : %s", now_obj_fmt)
    logging.info("query: lookback fmt       : %s", args["lookback"])
    logging.info("query: lookback seconds   : %d", lookback_seconds)
    logging.info("query: input_start local  : %s", args["input_start_fmt_local"])
    logging.info("query: input_end   local  : %s", args["input_end_fmt_local"])
    logging.info("query: start local        : %s", args["start_fmt_local"])
    logging.info("query: end   local        : %s", args["end_fmt_local"])
    logging.info("query: start utc          : %s", args["start_fmt"])
    logging.info("query: end   utc          : %s", args["end_fmt"])
    logging.info("query: time_range         : %s", delta)

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
        curl_cmd = curlify.to_curl(response.request).replace("-H 'Accept-Encoding: gzip, deflate'", "")
        logging.info("curl command: %s", curl_cmd)
        if response.status_code != 200:
            query_output["response"] = response.text
            logging.error(
                "Failed to query query_str=[%s] status_code=%s response_text=%s",
                query_str,
                response.status_code,
                response.text,
            )
        query_output["response"] = response.json()
        print(json.dumps(query_output, indent=2, default=str))
    return True


def main():
    """Main function"""
    args = load_args()

    if args["debug_run"]:
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    logging.debug("Dumping args: %s", json.dumps(args, default=str, indent=2))

    if not validate_args(args):
        return 1

    if not update_args(args):
        return 1

    if not query_url(args):
        return 1
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
