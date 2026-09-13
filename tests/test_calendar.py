"""Regression checks for GitHub HTML parsing and date/streak boundaries."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_contributions import parse_calendar, derive_stats


class CalendarTests(unittest.TestCase):
    def test_current_tooltips_not_dom_order(self):
        html = '''<td data-date="2026-09-13" data-level="1" id="b"></td>
        <td data-date="2026-09-12" data-level="0" id="a"></td>
        <tool-tip for="a">No contributions on September 12th.</tool-tip>
        <tool-tip for="b">1 contribution on September 13th.</tool-tip>'''
        days = parse_calendar(html)
        self.assertEqual([d["count"] for d in days], [0, 1])
        self.assertEqual(days[0]["date"], "2026-09-12")

    def test_legacy_counts_and_thousands(self):
        html = '''<rect data-date="2026-09-12" data-count="1,024" data-level="4"/>
        <td data-date="2026-09-13" id="a" data-level="4"></td>
        <tool-tip for="a">1,005 contributions on September 13th.</tool-tip>'''
        self.assertEqual([d["count"] for d in parse_calendar(html)], [1024, 1005])

    def test_missing_count_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "No contribution count"):
            parse_calendar('<td data-date="2026-09-13" data-level="4"></td>')

    def test_empty_or_gapped_response_fails(self):
        with self.assertRaises(ValueError):
            parse_calendar('<html>Service temporarily unavailable</html>')
        with self.assertRaisesRegex(ValueError, "missing dates"):
            parse_calendar('<rect data-date="2026-09-11" data-count="1"/><rect data-date="2026-09-13" data-count="1"/>')

    def test_current_streak_allows_today_to_be_unfinished(self):
        days = [{"date": f"2026-09-{d}", "count": c} for d,c in [(10, 0), (11, 4), (12, 7), (13, 0)]]
        stats = derive_stats(days, date(2026, 9, 13))
        self.assertEqual((stats["current_streak"],stats["longest_streak"],stats["total"]), (2,2,11))
        self.assertEqual(derive_stats(days, date(2026,9,14))["current_streak"], 0)

    def test_leap_day_and_month_boundary(self):
        days = [{"date": d, "count": c} for d,c in [("2024-02-28",2),("2024-02-29",3),("2024-03-01",4)]]
        stats = derive_stats(days,date(2024,3,1))
        self.assertEqual(stats["monthly_totals"],{"2024-02":5,"2024-03":4})
        self.assertEqual(stats["current_streak"],3)
        self.assertEqual(stats["best_day"],{"date":"2024-03-01","count":4})

    def test_future_days_excluded_from_stats(self):
        days = [{"date":"2026-09-13","count":2},{"date":"2026-09-14","count":100}]
        self.assertEqual(derive_stats(days,date(2026,9,13))["total"],2)


if __name__ == "__main__":
    unittest.main()
