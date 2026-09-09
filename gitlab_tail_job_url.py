#!/usr/bin/env python3

"""Resolve a GitLab job URL to a project ID and tail its log via gitlab_tail_job.py."""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

import requests

JOB_URL_SEP = "/-/jobs/"


def parse_job_url(job_url: str) -> dict:
    """Split a GitLab job URL into gitlab_url, project_path, and job_id."""
    parsed = urllib.parse.urlparse(job_url)
    scheme_host = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path
    project_path, _, job_part = path.partition(JOB_URL_SEP)
    job_id = job_part.strip("/").split("/")[0]
    return {
        "gitlab_url": scheme_host,
        "project_path": project_path.strip("/"),
        "job_id": job_id,
    }


def resolve_project_id(gitlab_url: str, project_path: str, token: str) -> str:
    """Look up a project's numeric ID by its URL-encoded namespace path."""
    encoded = urllib.parse.quote(project_path, safe="")
    resp = requests.get(
        f"{gitlab_url}/api/v4/projects/{encoded}",
        headers={"PRIVATE-TOKEN": token},
        timeout=30,
    )
    if resp.status_code != 200:
        logging.error("status=api_error http_status=%d body=%s", resp.status_code, resp.text)
        return ""
    project_id = str(resp.json()["id"])
    logging.info("status=resolved project_path=%s project_id=%s", project_path, project_id)
    return project_id


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(
        description="Resolve a GitLab job URL to a project ID and tail its log.",
    )
    parser.add_argument("job_url", help="Full GitLab job URL (e.g. https://host/group/proj/-/jobs/123)")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITLAB_PAT", os.environ.get("GITLAB_PAT", "")),
        help="GitLab private token (default: $GITLAB_PAT",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the resolved gitlab_tail_job.py command instead of running it",
    )
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    return vars(parser.parse_args())


def validate_args(args: dict) -> bool:
    """Validate arguments, return True if valid."""
    if not args["token"]:
        logging.error("status=validation_failed reason=missing_token hint=set_GITLAB_PAT")
        return False
    if JOB_URL_SEP not in args["job_url"]:
        logging.error("status=validation_failed reason=not_a_job_url expected_sep=%s", JOB_URL_SEP)
        return False
    return True


def update_args(args: dict) -> bool:
    """Parse the job URL into its components and store them on args."""
    parts = parse_job_url(args["job_url"])
    if not parts["job_id"].isdigit():
        logging.error("status=validation_failed reason=non_numeric_job_id job_id=%s", parts["job_id"])
        return False
    if not parts["project_path"]:
        logging.error("status=validation_failed reason=empty_project_path")
        return False
    args.update(parts)
    return True


def build_command(gitlab_url: str, job_id: str, project_id: str, interval: int, token: str) -> list[str]:
    """Build the gitlab_tail_job.py argument list."""
    tail_script = str(Path(__file__).resolve().parent / "gitlab_tail_job.py")
    return [
        sys.executable,
        tail_script,
        gitlab_url,
        job_id,
        "--project-id",
        project_id,
        "--interval",
        str(interval),
        "--token",
        token,
    ]


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

    project_id = resolve_project_id(args["gitlab_url"], args["project_path"], args["token"])
    if not project_id:
        logging.error("status=resolve_failed project_path=%s", args["project_path"])
        return 1

    command = build_command(args["gitlab_url"], args["job_id"], project_id, args["interval"], args["token"])

    if args["print_only"]:
        redacted = [part if part != args["token"] else "$GITLAB_PAT" for part in command]
        print(" ".join(redacted))
        return 0

    tail_script = command[1]
    if not Path(tail_script).is_file():
        logging.error("status=missing_dependency script=%s", tail_script)
        return 1
    if shutil.which(sys.executable) is None:
        logging.error("status=missing_interpreter interpreter=%s", sys.executable)
        return 1

    logging.info("status=tailing job_id=%s project_id=%s", args["job_id"], project_id)
    result = subprocess.run(command, check=False)  # noqa: S603
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
