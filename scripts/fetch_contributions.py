"""Read GitHub's public contribution calendar without a personal access token.

Reject malformed/incomplete responses rather than overwrite a good graph with
made-up zero counts. Supports current tool-tip cells and older data-count cells.
The live endpoint is public HTML, not a versioned API; the tests protect the
known forms and a changed response fails visibly in Actions.
"""
import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common import ROOT, config


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells = []
        self.tips = {}
        self.tip_for = None
        self.tip_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("td", "rect") and "data-date" in attrs:
            self.cells.append(attrs)
        if tag == "tool-tip":
            self.tip_for = attrs.get("for")
            self.tip_text = []

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tip_for:
            self.tips[self.tip_for] = " ".join(self.tip_text)
            self.tip_for = None

    def handle_data(self, data):
        if self.tip_for:
            self.tip_text.append(data)


def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    days = {}
    for cell in parser.cells:
        day = date.fromisoformat(cell["data-date"]).isoformat()
        if "data-count" in cell:
            count = int(cell["data-count"].replace(",", ""))
        else:
            label = parser.tips.get(cell.get("id"), "") or cell.get("aria-label", "")
            match = re.search(r"\b(No|[\d,]+)\s+contributions?\b", label, re.I)
            if not match:
                raise ValueError(f"No contribution count found for {day}; keeping the previous graph.")
            count = 0 if match[1].lower() == "no" else int(match[1].replace(",", ""))
        level = int(cell.get("data-level", min(count, 4)))
        if count < 0 or not 0 <= level <= 4:
            raise ValueError(f"Invalid contribution value for {day}")
        entry = {"date": day, "count": count, "level": level}
        if day in days and days[day] != entry:
            raise ValueError(f"Conflicting duplicate date: {day}")
        days[day] = entry
    if not days:
        raise ValueError("GitHub returned no calendar cells; keeping the previous graph.")
    ordered = [days[key] for key in sorted(days)]
    for left, right in zip(ordered, ordered[1:]):
        if (date.fromisoformat(right["date"]) - date.fromisoformat(left["date"])).days != 1:
            raise ValueError("Contribution calendar has missing dates.")
    return ordered


def derive_stats(days, today):
    past = [d for d in days if date.fromisoformat(d["date"]) <= today]
    if not past:
        raise ValueError("Contribution calendar contains no past or current days.")
    counts = {d["date"]: d["count"] for d in past}
    monthly = {}
    longest = run = 0
    for day in past:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)
        month = day["date"][:7]
        monthly[month] = monthly.get(month, 0) + day["count"]
    cursor = today if counts.get(today.isoformat(), 0) else today - timedelta(days=1)
    current = 0
    while counts.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    best = max(past, key=lambda d: d["count"])
    return {
        "total": sum(counts.values()),
        "active_days": sum(v > 0 for v in counts.values()),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly_totals": monthly,
    }


def fetch_html(username):
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", username):
        raise ValueError("Invalid GitHub username")
    url = f"https://github.com/users/{username}/contributions"
    req = Request(url, headers={"User-Agent": "github-profile-calendar/1.0", "Accept-Language": "en-US,en;q=0.9"})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=25) as response:
                payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError("Unexpectedly large calendar response")
            return payload.decode("utf-8")
        except (HTTPError, URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--html", type=Path, help="Parse an already downloaded response for offline validation")
    options = args.parse_args()
    username = config()["username"]
    html = options.html.read_text(encoding="utf-8") if options.html else fetch_html(username)
    today = datetime.now(timezone.utc).date()
    days = [d for d in parse_calendar(html) if date.fromisoformat(d["date"]) <= today]
    if not 350 <= len(days) <= 380:
        raise ValueError(f"Incomplete yearly calendar: {len(days)} days")
    last = date.fromisoformat(days[-1]["date"])
    if abs((today - last).days) > 1:
        raise ValueError(f"Stale calendar ending {last}; keeping the previous graph.")
    data = {
        "username": username,
        "source": f"https://github.com/users/{username}/contributions",
        "as_of": today.isoformat(),
        "period_start": days[0]["date"],
        "period_end": days[-1]["date"],
        "days": days,
        "stats": derive_stats(days, today),
    }
    target = ROOT / "data/contributions.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    print(f"Fetched {len(days)} days / {data['stats']['total']} contributions for {username}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, HTTPError, URLError, TimeoutError) as error:
        print(f"Calendar update failed: {error}", file=sys.stderr)
        sys.exit(1)
