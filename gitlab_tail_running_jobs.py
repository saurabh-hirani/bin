#!/usr/bin/env python3

"""Find a GitLab project's running jobs and tail each one in parallel."""

import argparse
import json
import logging
import os
import sys
import threading

from gitlab_find_project import find_projects
from gitlab_list_jobs import list_jobs
from gitlab_tail_job import tail_job


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(
        description="Find a GitLab project's running jobs and tail each one.",
    )
    parser.add_argument("gitlab_url", help="GitLab instance URL (e.g. https://gitlab.com)")
    parser.add_argument(
        "search_term", nargs="?", default="",
        help="Project name to search for (skip if --project-id given)",
    )
    parser.add_argument("--project-id", default="", help="GitLab project ID (skips search)")
    parser.add_argument("--ref", default="", help="Filter by branch/tag")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    parser.add_argument("--pipelines", type=int, default=3, help="Number of recent pipelines to check (default: 3)")
    parser.add_argument(
        "--token", default=os.environ.get("GITLAB_PAT", ""),
        help="GitLab private token (default: $GITLAB_PAT)",
    )
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    return vars(parser.parse_args())


def validate_args(args: dict) -> bool:
    """Validate arguments, return True if valid."""
    if not args["token"]:
        logging.error("status=validation_failed reason=missing_token hint=set_GITLAB_PAT_or_use_--token")
        return False
    if not args["search_term"] and not args["project_id"]:
        logging.error("status=validation_failed reason=must_provide_search_term_or_--project-id")
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

    # Step 1: resolve project ID
    project_id = args["project_id"]
    if project_id:
        logging.info("status=using_project_id project_id=%s", project_id)
    else:
        projects = find_projects(args["gitlab_url"], args["search_term"], args["token"])
        if not projects:
            logging.error("status=not_found search_term=%s", args["search_term"])
            return 1
        if len(projects) != 1:
            logging.error("status=ambiguous_project count=%d hint=use_--project-id", len(projects))
            json.dump(projects, sys.stderr, indent=2)
            sys.stderr.write("\n")
            return 1
        project_id = str(projects[0]["id"])
        logging.info("status=found_project project_id=%s path=%s", project_id, projects[0]["path_with_namespace"])

    # Step 2: list running jobs
    jobs = list_jobs(
        args["gitlab_url"], project_id, args["token"],
        status_list=["running"], ref=args["ref"], pipelines=args["pipelines"],
    )
    if not jobs:
        logging.info("status=no_running_jobs project_id=%s", project_id)
        return 0

    logging.info("status=found_running_jobs count=%d", len(jobs))

    # Step 3: tail each running job in parallel
    statuses: dict[str, str] = {}

    def _tail(job: dict) -> None:
        statuses[str(job["job_id"])] = tail_job(
            args["gitlab_url"], str(job["job_id"]), project_id, args["token"],
            interval=args["interval"], prefix=f"[{job['job_name']}] ",
        )

    threads = [threading.Thread(target=_tail, args=(j,)) for j in jobs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for job in jobs:
        jid = str(job["job_id"])
        logging.info(
            "status=result job_id=%s job_name=%s final_status=%s",
            jid, job["job_name"], statuses.get(jid, "unknown"),
        )

    return 0 if all(s == "success" for s in statuses.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
