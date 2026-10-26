from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StandaloneHtmlTests(unittest.TestCase):
    def test_embedded_translator_stays_in_sync_with_python_source(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        translator = (ROOT / "cobol2py.py").read_text(encoding="utf-8")
        match = re.search(
            r'<script type="text/plain" id="translator-source">\n([\s\S]*?)\n</script>',
            html,
        )
        self.assertIsNotNone(match, "HTML must contain the embedded translator source")
        self.assertEqual(match.group(1), translator)

    def test_browser_demo_does_not_call_the_local_translation_api(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("fetch('/api/translate'", html)
        self.assertIn("pyodide.runPythonAsync", html)
        self.assertIn(
            "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js",
            html,
        )


if __name__ == "__main__":
    unittest.main()
