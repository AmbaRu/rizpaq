
from __future__ import annotations

import unittest

from core import report_html


class TestReportHtml(unittest.TestCase):
    def test_escapes_user_data(self):
        payload = {
            "title": "Rizpaq <report>",
            "alerts": ["<script>alert(1)</script>"],
            "archives": [{
                "archive": 'F:/a&b"<x>.zpaq',
                "status": "ok",
            }],
        }
        text = report_html.render_dashboard_html(payload)
        self.assertIn("Rizpaq &lt;report&gt;", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>", text)
        self.assertIn("F:/a&amp;b&quot;&lt;x&gt;.zpaq", text)
        self.assertIn('class="ok"', text)

    def test_sections_and_numbers(self):
        payload = {
            "title": "Report",
            "summary": {"works": 2, "jobs": 5, "ok": 4, "error": 1,
                        "archives": 3},
            "archives": [{"work": "All", "job": "Weekly",
                          "archive": "F:/All.zpaq", "size": 1 << 30,
                          "status": "error", "reason": "PAR2"}],
            "runs": [{"date": "22.11", "work": "All", "job": "Weekly",
                      "status": "ok", "rc": 0}],
            "trend": [("22.11", 3, 1)],
            "size": [("22.11", 2 << 30)],
            "labels": {"archives": "ARCH", "runs": "RUNS"},
        }
        text = report_html.render_dashboard_html(payload)
        for needle in ("Report", "ARCH", "RUNS", "All", "F:/All.zpaq",
                       "1.0 GB", "2.0 GB", 'class="error"'):
            self.assertIn(needle, text)

    def test_empty_sections(self):
        text = report_html.render_dashboard_html({"title": "Empty"})
        self.assertIn("No data", text)
        self.assertIn('<p class="empty">—</p>', text)


if __name__ == "__main__":
    unittest.main()
