#!/usr/bin/env python3
"""List Fathom meetings with pagination support."""

import json
import logging
import os
import sys

import argparse
import requests
from datetime import datetime


def setup_logging(log_level: str) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


def load_credentials() -> dict:
    """Load credentials from credentials.json."""
    with open("credentials.json", "r") as f:
        return json.load(f)


def fetch_all_meetings(api_key: str, limit: int) -> list:
    """Fetch meetings with pagination until limit is reached."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    url = "https://api.fathom.ai/external/v1/meetings"
    all_meetings: list = []
    cursor = None

    while len(all_meetings) < limit:
        params: dict = {}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            logging.error("status=api_error code=%d body=%s", response.status_code, response.text)
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        all_meetings.extend(items)
        cursor = data.get("next_cursor")
        logging.debug("status=fetched_page items=%d total=%d has_next=%s", len(items), len(all_meetings), bool(cursor))

        if not cursor:
            break

    return all_meetings[:limit]


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(description="List Fathom meetings")
    parser.add_argument("--last", type=int, default=5, help="Number of meetings to list")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--prefix", help="Filter meetings by title prefix")
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    return vars(parser.parse_args())


def validate_args(args: dict) -> bool:
    """Validate arguments."""
    if args["last"] < 1:
        logging.error("status=validation_failed reason=last_must_be_positive")
        return False
    return True


def update_args(args: dict) -> bool:
    """Process arguments."""
    return True


def main() -> int:
    """Main function."""
    args = load_args()
    setup_logging(args["log_level"])

    if not validate_args(args):
        return 1

    if not update_args(args):
        return 1

    creds = load_credentials()
    api_key = creds["fathom_api_key"]

    # Fetch enough meetings to satisfy limit after filtering
    # If filtering by prefix, fetch more to account for filtered-out items
    fetch_limit = args["last"] * 10 if args["prefix"] else args["last"]
    meetings = fetch_all_meetings(api_key, fetch_limit)

    if args["prefix"]:
        meetings = [m for m in meetings if args["prefix"].lower() in m.get("title", "").lower()]

    meetings = meetings[: args["last"]]

    if args["json"]:
        print(json.dumps(meetings, indent=2))
    else:
        print(f"Latest {len(meetings)} meetings:\n")
        for i, meeting in enumerate(meetings, 1):
            title = meeting.get("title", "No title")
            meeting_title = meeting.get("meeting_title", "")
            created_at = meeting.get("created_at", "")
            meeting_url = meeting.get("url", "")
            recording_id = meeting.get("recording_id", "")
            recorded_by = meeting.get("recorded_by", {}).get("name", "Unknown")
            share_url = meeting.get("share_url", "")

            if created_at:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_date = "Unknown date"

            print(f"{i}. {title}")
            if meeting_title and meeting_title != title:
                print(f"   Meeting: {meeting_title}")
            print(f"   date: {formatted_date}")
            print(f"   recorded_by: {recorded_by}")
            print(f"   meeting_url: {meeting_url}")
            if share_url:
                print(f"   share_url: {share_url}")
            print(f"   recording_id: {recording_id}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
