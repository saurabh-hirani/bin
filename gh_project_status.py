"""Fetch and display status counts for all GitHub Projects V2 in an org."""

import argparse
import csv
import io
import json
import logging
import os
import sys
from collections import Counter

import requests

STATUS_ORDER = ["Backlog", "Pending", "In progress", "Blocked", "In review", "Done", "No Status"]


def load_args() -> dict:
    """Parse CLI arguments and return as dictionary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="JSON config file with CLI options")
    parser.add_argument("--org", required=True, help="GitHub org name")
    parser.add_argument("--project", nargs="+", help="Filter by project name(s) (substring match)")
    parser.add_argument("--format", default="markdown", choices=["json", "csv", "prettytable", "markdown"])
    parser.add_argument("--details", action="store_true", help="Show items per status per project")
    parser.add_argument("--per-status-table", action="store_true", help="Group all projects by status (one table per status)")
    parser.add_argument("--per-project-status-table", action="store_true", help="Within each project, one table per status")
    parser.add_argument("--status", nargs="+", help="Show only these statuses (with --details)")
    parser.add_argument("--skip-status", nargs="+", help="Skip these statuses (with --details)")
    parser.add_argument("--infer-start-date", action="store_true", help="Infer start date from 'moved to In progress' event via GraphQL")
    parser.add_argument(
        "--token-env",
        default="GITHUB_PROJECT_PAT",
        help="Env var holding the GitHub PAT",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = vars(parser.parse_args())
    if args["config"]:
        with open(args["config"]) as f:
            cfg = json.load(f)
        for k, v in cfg.items():
            k = k.replace("-", "_")
            if args.get(k) is None or (isinstance(args.get(k), bool) and not args[k]):
                args[k] = v
    return args


def validate_args(args: dict) -> bool:
    """Validate arguments, return True if valid."""
    token = os.environ.get(args["token_env"], "")
    if not token:
        logging.error("status=validation_failed reason=env_var_%s_not_set", args["token_env"])
        return False
    args["token"] = token
    return True


def update_args(args: dict) -> bool:
    """Process/enhance arguments, return True if successful."""
    args["base_url"] = f"https://api.github.com/orgs/{args['org']}/projectsV2"
    args["headers"] = {"Authorization": f"Bearer {args['token']}"}
    return True


def get_projects(args: dict) -> list[dict]:
    """Fetch all projects for the org."""
    resp = requests.get(args["base_url"], headers=args["headers"], timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_field_ids(args: dict, project_number: int) -> dict[str, int | None]:
    """Find Status and Start date field IDs for a project."""
    url = f"{args['base_url']}/{project_number}/fields"
    resp = requests.get(url, headers=args["headers"], timeout=30)
    resp.raise_for_status()
    ids: dict[str, int | None] = {"status": None, "start_date": None}
    for field in resp.json():
        if field.get("name") == "Status" and field.get("data_type") == "single_select":
            ids["status"] = field["id"]
        elif field.get("name") == "Start date" and field.get("data_type") == "date":
            ids["start_date"] = field["id"]
    return ids


def get_items_with_status(args: dict, project_number: int, field_ids: dict[str, int | None]) -> list[dict]:
    """Fetch all items with their status and start date."""
    items_out: list[dict] = []
    fields_param = ",".join(str(v) for v in field_ids.values() if v)
    url: str | None = f"{args['base_url']}/{project_number}/items?fields={fields_param}&per_page=100"
    while url:
        resp = requests.get(url, headers=args["headers"], timeout=30)
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break
        for item in items:
            status = "No Status"
            start_date = ""
            for f in item.get("fields", []):
                if f["id"] == field_ids["status"] and f.get("value"):
                    status = f["value"]["name"]["raw"]
                elif f["id"] == field_ids["start_date"] and f.get("value"):
                    start_date = f["value"]
            title = ""
            issue_url = ""
            assignees: list[dict] = []
            sub_tasks: list[dict] = []
            if item.get("content"):
                title = item["content"].get("title", "")
                issue_url = item["content"].get("html_url", "")
                for a in item["content"].get("assignees", []):
                    assignees.append({"login": a["login"], "url": a.get("html_url", "")})
                sis = item["content"].get("sub_issues_summary", {})
                if sis.get("total", 0) > 0:
                    api_url = item["content"].get("url", "")
                    if api_url:
                        sub_resp = requests.get(f"{api_url}/sub_issues", headers=args["headers"], timeout=30)
                        if sub_resp.status_code == 200:
                            for si in sub_resp.json():
                                sub_tasks.append({
                                    "title": si.get("title", ""),
                                    "state": si.get("state", ""),
                                    "url": si.get("html_url", ""),
                                })
            items_out.append({"title": title, "status": status, "start_date": start_date, "url": issue_url, "assignees": assignees, "sub_tasks": sub_tasks})
        url = resp.links.get("next", {}).get("url")
    return items_out


def get_in_progress_date(args: dict, owner: str, repo: str, issue_number: int) -> str:
    """Get the date when an issue was first moved to 'In progress' via GraphQL."""
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          timelineItems(itemTypes: [PROJECT_V2_ITEM_STATUS_CHANGED_EVENT], first: 50) {
            nodes {
              ... on ProjectV2ItemStatusChangedEvent {
                createdAt
                status
              }
            }
          }
        }
      }
    }
    """
    resp = requests.post(
        "https://api.github.com/graphql",
        headers=args["headers"],
        json={"query": query, "variables": {"owner": owner, "repo": repo, "number": issue_number}},
        timeout=30,
    )
    if resp.status_code != 200:
        return ""
    data = resp.json()
    nodes = (data.get("data") or {}).get("repository", {}).get("issue", {}).get("timelineItems", {}).get("nodes", [])
    for node in nodes:
        if node.get("status") == "In progress":
            return node.get("createdAt", "")
    return ""


def infer_start_dates(args: dict, items: list[dict]) -> list[dict]:
    """For items without start_date that are In progress, infer from timeline."""
    for item in items:
        if item["start_date"] or item["status"] != "In progress":
            continue
        url = item.get("url", "")
        if not url:
            continue
        # Parse owner/repo/number from html_url like https://github.com/org/repo/issues/13
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) < 4:
            continue
        owner, repo, issue_number = parts[0], parts[1], int(parts[3])
        date = get_in_progress_date(args, owner, repo, issue_number)
        if date:
            item["start_date"] = date
            logging.info("status=inferred_start_date issue=%s/%s#%d date=%s", owner, repo, issue_number, date)
    return items


def format_date(date_str: str) -> str:
    """Convert ISO date to human readable format like '04th May 2026'."""
    if not date_str:
        return ""
    from datetime import datetime

    dt = datetime.fromisoformat(date_str)
    day = dt.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day:02d}{suffix} {dt.strftime('%b %Y')}"


def sort_key(status: str) -> int:
    """Return sort order for a status."""
    try:
        return STATUS_ORDER.index(status)
    except ValueError:
        return len(STATUS_ORDER)


def has_sub_tasks(results: list[dict]) -> bool:
    """Check if any item in results has sub-tasks."""
    for r in results:
        for item in r.get("items", []):
            if item.get("sub_tasks"):
                return True
    return False


def fmt_assignees(assignees: list[dict], as_markdown: bool = False) -> str:
    """Format assignees list as a string."""
    if not assignees:
        return "-"
    if as_markdown:
        return ", ".join(f"[@{a['login']}]({a['url']})" for a in assignees)
    return ", ".join(a["login"] for a in assignees)


def format_json(results: list[dict], details: bool, per_status_table: bool, per_project_status_table: bool) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def format_csv(results: list[dict], details: bool, per_status_table: bool, per_project_status_table: bool) -> str:
    """Format results as CSV."""
    buf = io.StringIO()
    if details:
        writer = csv.writer(buf)
        writer.writerow(["project", "status", "title", "start_date"])
        for r in results:
            for item in r.get("items", []):
                writer.writerow([r["project"], item["status"], item["title"], format_date(item["start_date"])])
    else:
        writer = csv.writer(buf)
        writer.writerow(["project", "status", "count"])
        for r in results:
            for status in sorted(r["status_counts"], key=sort_key):
                writer.writerow([r["project"], status, r["status_counts"][status]])
    return buf.getvalue().rstrip()


def format_prettytable(results: list[dict], details: bool, per_status_table: bool, per_project_status_table: bool) -> str:
    """Format results using PrettyTable."""
    from prettytable import PrettyTable

    show_sub = has_sub_tasks(results)

    def _item_rows(item: dict) -> list[list[str]]:
        """Return rows for an item. One row per sub-task if any."""
        base = [item["title"], fmt_assignees(item.get("assignees", [])), format_date(item["start_date"]) or "-"]
        if not show_sub:
            return [base]
        subs = item.get("sub_tasks", [])
        if not subs:
            return [base + ["-", "-"]]
        rows = []
        for st in subs:
            rows.append(base + [st["title"], st["state"]])
        return rows

    if details and per_status_table:
        all_items: list[tuple[str, str, dict]] = []
        for r in results:
            for item in r.get("items", []):
                all_items.append((item["status"], r["project"], item))
        sections: list[str] = []
        grouped: dict[str, list[tuple[str, dict]]] = {}
        for status, project, item in all_items:
            grouped.setdefault(status, []).append((project, item))
        for status in sorted(grouped, key=sort_key):
            cols = ["Project", "Task", "Assignee", "Start Date"] + (["Sub-task", "State"] if show_sub else [])
            t = PrettyTable(cols)
            t.align = "l"
            t.title = status
            for project, item in grouped[status]:
                for row in _item_rows(item):
                    t.add_row([project] + row)
            sections.append(t.get_string())
        return "\n\n".join(sections)
    elif details and per_project_status_table:
        sections: list[str] = []
        for r in results:
            grouped: dict[str, list[dict]] = {}
            for item in r.get("items", []):
                grouped.setdefault(item["status"], []).append(item)
            for status in sorted(grouped, key=sort_key):
                cols = ["Task", "Assignee", "Start Date"] + (["Sub-task", "State"] if show_sub else [])
                t = PrettyTable(cols)
                t.align = "l"
                t.title = f"{r['project']} - {status}"
                for item in grouped[status]:
                    for row in _item_rows(item):
                        t.add_row(row)
                sections.append(t.get_string())
        return "\n\n".join(sections)
    elif details:
        sections: list[str] = []
        for r in results:
            cols = ["Status", "Task", "Assignee", "Start Date"] + (["Sub-task", "State"] if show_sub else [])
            t = PrettyTable(cols)
            t.align = "l"
            t.title = f"{r['project']} (#{r['number']})"
            grouped: dict[str, list[dict]] = {}
            for item in r.get("items", []):
                grouped.setdefault(item["status"], []).append(item)
            for status in sorted(grouped, key=sort_key):
                for item in grouped[status]:
                    for row in _item_rows(item):
                        t.add_row([status] + row)
            sections.append(t.get_string())
        return "\n\n".join(sections)
    else:
        t = PrettyTable(["Project", "Backlog", "Pending", "In progress", "Blocked", "In review", "Done", "No Status"])
        t.align = "l"
        for r in results:
            c = r["status_counts"]
            t.add_row([
                r["project"],
                c.get("Backlog", 0),
                c.get("Pending", 0),
                c.get("In progress", 0),
                c.get("Blocked", 0),
                c.get("In review", 0),
                c.get("Done", 0),
                c.get("No Status", 0),
            ])
        return t.get_string()


def format_markdown(results: list[dict], details: bool, per_status_table: bool, per_project_status_table: bool) -> str:
    """Format results as markdown."""
    lines: list[str] = []
    show_sub = has_sub_tasks(results)

    def _md_rows(item: dict) -> list[str]:
        """Return markdown table rows for item, one per sub-task."""
        t_link = f"[{item['title']}]({item['url']})" if item["url"] else item["title"]
        assignee = fmt_assignees(item.get("assignees", []), as_markdown=True)
        date = format_date(item["start_date"]) or "-"
        subs = item.get("sub_tasks", [])
        if not show_sub:
            return [f"| {t_link} | {assignee} | {date} |"]
        if not subs:
            return [f"| {t_link} | {assignee} | {date} | - | - |"]
        rows = []
        for st in subs:
            st_link = f"[{st['title']}]({st['url']})" if st["url"] else st["title"]
            rows.append(f"| {t_link} | {assignee} | {date} | {st_link} | {st['state']} |")
        return rows

    sub_hdr = " Sub-task | State |" if show_sub else ""
    sub_sep = "----------|-------|" if show_sub else ""

    if details and per_status_table:
        all_items: list[tuple[str, str, str, dict]] = []
        for r in results:
            for item in r.get("items", []):
                all_items.append((item["status"], r["project"], r["project_url"], item))
        grouped: dict[str, list[tuple[str, str, dict]]] = {}
        for status, project, project_url, item in all_items:
            grouped.setdefault(status, []).append((project, project_url, item))
        for status in sorted(grouped, key=sort_key):
            lines.append(f"## {status}")
            lines.append("")
            lines.append(f"| Project | Task | Assignee | Start Date |{sub_hdr}")
            lines.append(f"|---------|------|----------|------------|{sub_sep}")
            for project, project_url, item in grouped[status]:
                p_link = f"[{project}]({project_url})"
                t_link = f"[{item['title']}]({item['url']})" if item["url"] else item["title"]
                assignee = fmt_assignees(item.get("assignees", []), as_markdown=True)
                date = format_date(item["start_date"]) or "-"
                subs = item.get("sub_tasks", [])
                if not show_sub:
                    lines.append(f"| {p_link} | {t_link} | {assignee} | {date} |")
                elif not subs:
                    lines.append(f"| {p_link} | {t_link} | {assignee} | {date} | - | - |")
                else:
                    for st in subs:
                        st_link = f"[{st['title']}]({st['url']})" if st["url"] else st["title"]
                        lines.append(f"| {p_link} | {t_link} | {assignee} | {date} | {st_link} | {st['state']} |")
            lines.append("")
    elif details and per_project_status_table:
        for r in results:
            p_link = f"[{r['project']}]({r['project_url']})"
            lines.append(f"## {p_link} (#{r['number']})")
            lines.append("")
            grouped: dict[str, list[dict]] = {}
            for item in r.get("items", []):
                grouped.setdefault(item["status"], []).append(item)
            for status in sorted(grouped, key=sort_key):
                lines.append(f"### {status}")
                lines.append("")
                lines.append(f"| Task | Assignee | Start Date |{sub_hdr}")
                lines.append(f"|------|----------|------------|{sub_sep}")
                for item in grouped[status]:
                    lines.extend(_md_rows(item))
                lines.append("")
    elif details:
        for r in results:
            p_link = f"[{r['project']}]({r['project_url']})"
            lines.append(f"## {p_link} (#{r['number']})")
            lines.append("")
            lines.append(f"| Status | Task | Assignee | Start Date |{sub_hdr}")
            lines.append(f"|--------|------|----------|------------|{sub_sep}")
            grouped: dict[str, list[dict]] = {}
            for item in r.get("items", []):
                grouped.setdefault(item["status"], []).append(item)
            for status in sorted(grouped, key=sort_key):
                for item in grouped[status]:
                    t_link = f"[{item['title']}]({item['url']})" if item["url"] else item["title"]
                    assignee = fmt_assignees(item.get("assignees", []), as_markdown=True)
                    date = format_date(item["start_date"]) or "-"
                    subs = item.get("sub_tasks", [])
                    if not show_sub:
                        lines.append(f"| {status} | {t_link} | {assignee} | {date} |")
                    elif not subs:
                        lines.append(f"| {status} | {t_link} | {assignee} | {date} | - | - |")
                    else:
                        for st in subs:
                            st_link = f"[{st['title']}]({st['url']})" if st["url"] else st["title"]
                            lines.append(f"| {status} | {t_link} | {assignee} | {date} | {st_link} | {st['state']} |")
            lines.append("")
    else:
        lines.append("| Project | Backlog | Pending | In progress | Blocked | In review | Done | No Status |")
        lines.append("|---------|---------|---------|-------------|---------|-----------|------|-----------|")
        for r in results:
            c = r["status_counts"]
            p_link = f"[{r['project']}]({r['project_url']})"
            lines.append(
                f"| {p_link} | {c.get('Backlog', 0)} | {c.get('Pending', 0)} | "
                f"{c.get('In progress', 0)} | {c.get('Blocked', 0)} | {c.get('In review', 0)} | "
                f"{c.get('Done', 0)} | {c.get('No Status', 0)} |"
            )
    return "\n".join(lines)


def main() -> int:
    """Main function returning exit code."""
    args = load_args()
    logging.basicConfig(
        level=args["log_level"],
        format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    if not validate_args(args):
        return 1
    if not update_args(args):
        return 1

    projects = get_projects(args)
    logging.info("status=fetched_projects count=%d", len(projects))

    results = []
    if args["project"]:
        filters = [f.lower() for f in args["project"]]
        projects = [p for p in projects if any(f in p["title"].lower() for f in filters)]
        # Sort by the order specified in --project
        def _project_order(p: dict) -> int:
            for i, f in enumerate(filters):
                if f in p["title"].lower():
                    return i
            return len(filters)
        projects.sort(key=_project_order)
        logging.info("status=filtered_projects count=%d filter=%s", len(projects), args["project"])

    for proj in projects:
        logging.info("status=processing project=%s", proj["title"])
        field_ids = get_field_ids(args, proj["number"])
        if field_ids["status"] is None:
            logging.warning("status=no_status_field project=%s", proj["title"])
            continue
        items = get_items_with_status(args, proj["number"], field_ids)
        if args["infer_start_date"]:
            items = infer_start_dates(args, items)
        counts = Counter(i["status"] for i in items)
        logging.info("status=fetched project=%s items=%d", proj["title"], len(items))
        project_url = f"https://github.com/orgs/{args['org']}/projects/{proj['number']}"
        entry: dict = {"project": proj["title"], "number": proj["number"], "project_url": project_url, "status_counts": dict(counts)}
        if args["details"]:
            filtered = items
            if args["status"]:
                allowed = [s.lower() for s in args["status"]]
                filtered = [i for i in filtered if i["status"].lower() in allowed]
            if args["skip_status"]:
                skipped = [s.lower() for s in args["skip_status"]]
                filtered = [i for i in filtered if i["status"].lower() not in skipped]
            entry["items"] = sorted(filtered, key=lambda x: sort_key(x["status"]))
        results.append(entry)

    formatters = {"json": format_json, "csv": format_csv, "prettytable": format_prettytable, "markdown": format_markdown}
    print(formatters[args["format"]](results, args["details"], args["per_status_table"], args["per_project_status_table"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
