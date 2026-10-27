from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AgentHtmlTests(unittest.TestCase):
    def test_standalone_agent_ui_has_local_file_analysis_and_exports(self):
        html = (ROOT / "web" / "agent.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="es">', html)
        self.assertIn('type="file" multiple', html)
        self.assertIn('await f.text()', html)
        self.assertIn('cobol2py-browser-inventory.json', html)
        self.assertIn('cobol2py-browser-inventory.md', html)
        self.assertIn('unresolved_references', html)
        self.assertIn('ambiguous_references', html)
        self.assertIn('dynamic_calls', html)
        self.assertIn('dynamic_call_targets', html)
        self.assertIn('id="dynamic"', html)
        self.assertIn('id="result-filter"', html)
        self.assertIn('filtered-out', html)
        self.assertIn('function maskLiterals', html)
        self.assertIn('literalCalls(clean,code)', html)
        self.assertIn('No se ejecuta', html) if 'No se ejecuta' in html else self.assertIn('no ejecuta', html.lower())

    def test_agent_ui_does_not_send_source_to_a_server(self):
        html = (ROOT / "web" / "agent.html").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertIn("procesa localmente", html)


if __name__ == "__main__":
    unittest.main()
