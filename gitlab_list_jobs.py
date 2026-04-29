#!/usr/bin/env python3

"""List active GitLab CI jobs across a project's last N pipelines."""

import argparse
import json
import logging
import os
import sys

import requests


def list_jobs(
    gitlab_url: str,
    project_id: str,
    token: str,
    status_list: list[str] | None = None,
    ref: str = "",
    pipelines: int = 3,
) -> list[dict]:
    """List active CI jobs across a project's last N pipelines. Returns list of job dicts."""
    if status_list is None:
        status_list = ["running", "pending", "created"]

    headers = {"PRIVATE-TOKEN": token}
    base = f"{gitlab_url}/api/v4/projects/{project_id}"

    params: dict = {"per_page": pipelines}
    if ref:
        params["ref"] = ref

    resp = requests.get(f"{base}/pipelines", headers=headers, params=params, timeout=30)
    if resp.status_code != 200:
        logging.error("status=api_error http_status=%d body=%s", resp.status_code, resp.text)
        return []

    pipeline_list = resp.json()
    if not pipeline_list:
        logging.error("status=no_pipelines_found")
        return []

    results = []
    for pipeline in pipeline_list:
        pid = pipeline["id"]
        resp = requests.get(f"{base}/pipelines/{pid}/jobs", headers=headers, params={"per_page": 100}, timeout=30)
        if resp.status_code != 200:
            logging.error("status=api_error pipeline_id=%d http_status=%d", pid, resp.status_code)
            continue
        for job in resp.json():
            if job["status"] in status_list:
                results.append(
                    {
                        "pipeline_id": pid,
                        "job_id": job["id"],
                        "job_name": job["name"],
                        "status": job["status"],
                        "stage": job["stage"],
                        "ref": job["ref"],
                    }
                )

    logging.info("status=complete active_jobs_found=%d", len(results))
    return results


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(
        description="List active GitLab CI jobs for a project's recent pipelines.",
    )
    parser.add_argument("gitlab_url", help="GitLab instance URL (e.g. https://gitlab.com)")
    parser.add_argument("--project-id", required=True, help="GitLab project ID")
    parser.add_argument("--ref", default="", help="Filter by branch/tag")
    parser.add_argument(
        "--status",
        default="running,pending,created",
        help="Comma-separated job status filter (default: running,pending,created)",
    )
    parser.add_argument("--pipelines", type=int, default=3, help="Number of recent pipelines to check (default: 3)")
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


def update_args(args: dict) -> bool:
    """Process arguments."""
    args["status_list"] = [s.strip() for s in args["status"].split(",")]
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

    results = list_jobs(
        args["gitlab_url"],
        args["project_id"],
        args["token"],
        status_list=args["status_list"],
        ref=args["ref"],
        pipelines=args["pipelines"],
    )
    json.dump(results, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
