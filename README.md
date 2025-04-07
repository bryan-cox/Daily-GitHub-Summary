# GitHub Daily Summary

A Python CLI tool to generate a daily (or date range) activity summary for a GitHub user. It retrieves pull request activity, reviews, and comments for the specified date or date range.

## 🔧 Requirements

- Python 3.7+
- Set the `GITHUB_TOKEN` environment variable with a [personal access token](https://github.com/settings/tokens) that has permission to read public events.

```bash
export GITHUB_TOKEN=your_token_here
```

## 🚀 Usage

```bash
python github-daily-summary.py --user USERNAME --start-date YYYY-MM-DD [--end-date YYYY-MM-DD] [--output json|markdown] [--summary]
```

### Required Flags

- `--user`: GitHub username to fetch activity for.
- `--start-date`: Start date for the summary in `YYYY-MM-DD` format.

### Optional Flags

- `--end-date`: End date for the summary. If omitted, only `start-date` will be used.
- `--output`: Output format. Options are:
  - `json` (default)
  - `markdown`
- `--summary`: When used with `--output markdown`, this flag summarizes PR comment activity by PR rather than listing every comment.

---

## 🧪 Examples

### Get activity for one day in markdown

```bash
python github-daily-summary.py --user bryan-cox --start-date 2025-04-04 --output markdown
```

### Get activity over a date range in markdown format

```bash
python github-daily-summary.py --user bryan-cox --start-date 2025-04-01 --end-date 2025-04-04 --output markdown
```

### Get a JSON summary for a range of dates

```bash
python github-daily-summary.py --user bryan-cox --start-date 2025-04-01 --end-date 2025-04-04
```

### Summarized PR comments per day

```bash
python github-daily-summary.py --user bryan-cox --start-date 2025-04-04 --output markdown --summary
```

---

## 📦 Output Examples

### Markdown Output (with `--summary`)
```
## 2025-04-04

### Pull Requests Opened
- [Fix race condition in cache logic](https://github.com/org/repo/pull/123)

### Pull Requests Reviewed
- [Refactor logging module](https://github.com/org/repo/pull/124)
```

### JSON Output
```json
[
  {
    "date": "2025-04-04",
    "summary": {
      "prs_opened": [...],
      "prs_closed": [...],
      "prs_reviewed": [...],
      "pr_comments": {...},
      "general_comments": [...]
    }
  }
]
```

---

## 🐞 Notes

- GitHub only allows access to the last 300 public events per user.
- Only events for pull requests, reviews, and comments are included.
- Authenticated with your `GITHUB_TOKEN` to avoid API rate limits.
- Same day events may be limited and not up to date.