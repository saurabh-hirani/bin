#!/usr/bin/env python3

"""Tail a GitLab CI job's log output, polling until the job completes."""

import argparse
import logging
import os
import sys
import time
import typing

import requests

TERMINAL_STATUSES = {"success", "failed", "canceled", "skipped"}


def tail_job(
    gitlab_url: str,
    job_id: str,
    project_id: str,
    token: str,
    interval: int = 5,
    output: typing.TextIO = sys.stdout,
    prefix: str = "",
) -> str:
    """Tail a GitLab CI job's log, polling until complete. Returns final job status."""
    headers = {"PRIVATE-TOKEN": token}
    base = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}"
    logging.info("status=tailing job_id=%s project_id=%s interval=%ds", job_id, project_id, interval)

    prev_len = 0
    while True:
        resp = requests.get(base, headers=headers, timeout=30)
        if resp.status_code != 200:
            logging.error("status=api_error http_status=%d body=%s", resp.status_code, resp.text)
            return "error"
        status = resp.json()["status"]

        trace = requests.get(f"{base}/trace", headers=headers, timeout=30)
        if trace.status_code != 200:
            logging.error("status=trace_error http_status=%d", trace.status_code)
            return "error"
        log = trace.text

        if len(log) > prev_len:
            new_text = log[prev_len:]
            if prefix:
                new_text = "".join(f"{prefix}{line}\n" for line in new_text.splitlines())
            output.write(new_text)
            output.flush()
            prev_len = len(log)

        if status in TERMINAL_STATUSES:
            logging.info("status=complete job_status=%s", status)
            return status

        time.sleep(interval)


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(
        description="Tail a GitLab CI job's log output, polling until the job completes.",
    )
    parser.add_argument("gitlab_url", help="GitLab instance URL (e.g. https://gitlab.com)")
    parser.add_argument("job_id", help="Numeric job ID")
    parser.add_argument("--project-id", required=True, help="GitLab project ID")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITLAB_PAT", ""),
        help="GitLab private token (default: $GITLAB_PAT)",
    )
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    return vars(parser.parse_args())


def validate_args(args: dict) -> bool:
    """Validate arguments, return True if valid."""
    if not args["token"]:
        logging.error("status=validation_failed reason=missing_token hint=set_GITLAB_PAT_or_use_--token")
        return False
    return True


def update_args(args: dict) -> bool:  # noqa: ARG001
    """Process arguments."""
    return True


def main() -> int:
    """Main function returning exit code."""
    args = load_args()
    logging.basicConfig(
        level=getattr(logging, args["log_level"].upper()),
        format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )

    if not validate_args(args):
        return 1
    if not update_args(args):
        return 1

    status = tail_job(args["gitlab_url"], args["job_id"], args["project_id"], args["token"], args["interval"])
    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
