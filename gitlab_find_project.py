#!/usr/bin/env python3

"""Search GitLab projects by name and return project IDs."""

import argparse
import json
import logging
import os
import sys

import requests


def find_projects(gitlab_url: str, search_term: str, token: str) -> list[dict]:
    """Search GitLab projects by name. Returns list of {id, path_with_namespace} (max 100)."""
    resp = requests.get(
        f"{gitlab_url}/api/v4/projects",
        headers={"PRIVATE-TOKEN": token},
        params={"search": search_term, "per_page": 100},
        timeout=30,
    )
    if resp.status_code != 200:
        logging.error("status=api_error http_status=%d body=%s", resp.status_code, resp.text)
        return []

    projects = resp.json()
    logging.info("status=found count=%d", len(projects))
    return [{"id": project["id"], "path_with_namespace": project["path_with_namespace"]} for project in projects]


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(
        description="Search GitLab projects by name and return project IDs.",
    )
    parser.add_argument("gitlab_url", help="GitLab instance URL (e.g. https://gitlab.com)")
    parser.add_argument("search_term", help="Project name to search for")
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

    results = find_projects(args["gitlab_url"], args["search_term"], args["token"])
    if not results:
        logging.error("status=not_found search_term=%s", args["search_term"])
        return 1

    json.dump(results, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
