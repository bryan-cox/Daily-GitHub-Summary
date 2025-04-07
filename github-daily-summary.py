import requests
import datetime
import pytz
import sys
import json
import os
import argparse
from dateutil import parser as date_parser
from collections import defaultdict

def get_github_daily_summary(username, date, output_format="json", summary_mode=False):
    token = os.environ.get('GITHUB_TOKEN')
    if token is None:
        return "Error: GITHUB_TOKEN environment variable not set."

    headers = {"Authorization": f"token {token}"}
    base_url = "https://api.github.com"

    # Convert the input date to UTC time range
    utc = pytz.utc
    start_of_day_utc = utc.localize(datetime.datetime.combine(date, datetime.time.min))
    end_of_day_utc = utc.localize(datetime.datetime.combine(date, datetime.time.max))

    events_url = f"{base_url}/users/{username}/events?per_page=100"
    response = requests.get(events_url, headers=headers)

    try:
        events = response.json()
    except ValueError:
        return f"Error: Invalid JSON response from GitHub API. Response: {response.text}"

    if not isinstance(events, list):
        return "Error: GitHub API returned an unexpected response."

    pr_events = defaultdict(list)
    general_events = []
    all_pr_comments = []

    for event in events:
        try:
            event_time_utc = date_parser.parse(event["created_at"]).astimezone(pytz.utc)
        except Exception as e:
            continue

        if start_of_day_utc <= event_time_utc <= end_of_day_utc:
            if event["type"] == "PullRequestEvent":
                pr_data = event["payload"]["pull_request"]
                pr_events[pr_data["html_url"]].append((event_time_utc, event))
            elif event["type"] == "PullRequestReviewEvent":
                pr_data = event["payload"]["pull_request"]
                pr_events[pr_data["html_url"]].append((event_time_utc, event))
            elif event["type"] == "IssueCommentEvent" and "/pull/" in event["payload"]["issue"]["html_url"]:
                pr_data = event["payload"]["issue"]["pull_request"]["html_url"]
                all_pr_comments.append((event_time_utc, event))
                pr_events[pr_data].append((event_time_utc, event))
            else:
                general_events.append((event_time_utc, event))

    summary = {
        "prs_opened": [],
        "prs_closed": [],
        "prs_reviewed": [],
        "pr_comments": defaultdict(list),
        "general_comments": []
    }

    pr_title_map = {}
    prs_opened_urls = set()
    prs_processed_urls = set()  # Add this set to track processed PR URLs

    for pr_url, timed_events in pr_events.items():
        timed_events.sort(key=lambda x: x[0])
        for time_utc, event in timed_events:
            if event["type"] == "PullRequestEvent":
                pr_data = event["payload"]["pull_request"]
                pr_url = pr_data["html_url"]
                if pr_url not in prs_processed_urls:  # Check if the PR has been processed already
                    pr_title_map[pr_url] = pr_data["title"]
                    if event["payload"]["action"] == "opened":
                        summary["prs_opened"].append(f"[{pr_data['title']}]({pr_url})")
                        prs_opened_urls.add(pr_url)
                    elif event["payload"]["action"] == "closed":
                        summary["prs_closed"].append(f"[{pr_data['title']}]({pr_url})")
                    prs_processed_urls.add(pr_url)  # Mark as processed
            elif event["type"] == "PullRequestReviewEvent":
                pr_data = event["payload"]["pull_request"]
                pr_url = pr_data["html_url"]
                if pr_url not in prs_processed_urls and pr_url not in prs_opened_urls:
                    summary["prs_reviewed"].append(f"[{pr_data['title']}]({pr_url})")
                    prs_processed_urls.add(pr_url)  # Mark as processed
            elif event["type"] == "IssueCommentEvent" and "/pull/" in event["payload"]["issue"]["html_url"]:
                pr_url = event["payload"]["issue"]["pull_request"]["html_url"]
                if pr_url not in prs_processed_urls:
                    pr_title_map[pr_url] = event["payload"]["issue"]["title"]
                    comment_body = event["payload"]["comment"]["body"]
                    summary["pr_comments"][pr_url].append(f"Comment: {comment_body}")
                    prs_processed_urls.add(pr_url)  # Mark as processed

    general_events.sort(key=lambda x: x[0])
    for time_utc, event in general_events:
        if event["type"] == "IssueCommentEvent":
            comment_body = event["payload"]["comment"]["body"]
            summary["general_comments"].append(f"Comment: {comment_body}")

    if output_format == "markdown":
        markdown_output = ""
        if summary["prs_opened"]:
            markdown_output += "### Pull Requests Opened\n"
            for pr in summary["prs_opened"]:
                markdown_output += f"- {pr}\n"
        if summary["prs_closed"]:
            markdown_output += "### Pull Requests Closed\n"
            for pr in summary["prs_closed"]:
                markdown_output += f"- {pr}\n"
        if summary["prs_reviewed"]:
            markdown_output += "### Pull Requests Reviewed\n"
            for pr in summary["prs_reviewed"]:
                markdown_output += f"- {pr}\n"
        if summary["pr_comments"]:
            if summary_mode:
                markdown_output += "### Commented on Pull Requests\n"
                for pr_url in summary["pr_comments"]:
                    pr_title = pr_title_map.get(pr_url, pr_url)
                    markdown_output += f"- [{pr_title}]({pr_url})\n"
            else:
                markdown_output += "### Pull Request Comments\n"
                comment_groups = defaultdict(list)
                for time_utc, event in all_pr_comments:
                    pr_url = event["payload"]["issue"]["pull_request"]["html_url"]
                    pr_title = event["payload"]["issue"]["title"]
                    comment_body = event["payload"]["comment"]["body"]
                    comment_groups[pr_url].append((time_utc, f"Comment: {comment_body}"))
                for pr_url, comments in comment_groups.items():
                    comments.sort(key=lambda x: x[0])
                    pr_title = pr_title_map.get(pr_url, pr_url)
                    markdown_output += f"- [{pr_title}]({pr_url})\n"
                    for time_utc, comment in comments:
                        markdown_output += f"    - {comment}\n"
        if summary["general_comments"]:
            markdown_output += "### General Comments\n"
            for comment in summary["general_comments"]:
                markdown_output += f"- {comment}\n"
        return markdown_output
    else:
        return summary


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + datetime.timedelta(n)

# Parse CLI args
arg_parser = argparse.ArgumentParser(description="Retrieve GitHub daily activity summary.")
arg_parser.add_argument("--user", required=True, help="GitHub username")
arg_parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
arg_parser.add_argument("--end-date", required=False, help="End date (YYYY-MM-DD)")
arg_parser.add_argument("--output", choices=["json", "markdown"], default="json", help="Output format")
arg_parser.add_argument("--summary", action="store_true", help="Show summary mode for PR comments")

args = arg_parser.parse_args()

try:
    start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else start_date
except ValueError:
    print("Invalid date format. Please use YYYY-MM-DD.")
    sys.exit(1)

if start_date > end_date:
    print("Error: Start date cannot be after end date.")
    sys.exit(1)

output_format = args.output
summary_mode = args.summary

if summary_mode and output_format != "markdown":
    print("Error: --summary flag is only valid with markdown output.")
    sys.exit()

if output_format == "markdown":
    print(f"# GitHub Activity for {args.user}\n")
    for single_date in daterange(start_date, end_date):
        print(f"## {single_date.strftime('%Y-%m-%d')}")
        print(get_github_daily_summary(args.user, single_date, output_format, summary_mode))
        print()
else:
    combined_json = []
    for single_date in daterange(start_date, end_date):
        summary = get_github_daily_summary(args.user, single_date, output_format, summary_mode)
        combined_json.append({
            "date": single_date.isoformat(),
            "summary": summary
        })
    print(json.dumps(combined_json, indent=2))
