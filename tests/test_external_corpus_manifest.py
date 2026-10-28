"""Regression tests for external COBOL candidate provenance metadata."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "external-corpus" / "candidates.json"
VALIDATOR = ROOT / "tools" / "validate_external_corpus_manifest.py"


class ExternalCorpusManifestTests(unittest.TestCase):
    def test_committed_candidate_ledger_is_valid_and_not_claimed_as_tested(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["entries"]), 6)
        self.assertTrue(all(item["compile_status"] == "NOT_RUN" for item in manifest["entries"]))
        self.assertTrue(all(item["runtime_status"] == "NOT_RUN" for item in manifest["entries"]))
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_unpinned_or_invalid_source_metadata(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("external_manifest_validator", VALIDATOR)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        bad = {
            "entries": [{
                "id": "bad", "project": "Bad", "program_id": "BAD",
                "repository": "example/bad", "source_path": "bad.cob",
                "source_url": "https://github.com/example/bad/blob/0123456789012345678901234567890123456789/bad.cob",
                "source_commit": "main", "source_blob_sha": "invalid",
                "source_lines": 0, "license_spdx": "MIT", "license_path": "LICENSE",
                "license_evidence": "checked", "compile_status": "NOT_RUN",
                "runtime_status": "NOT_RUN",
            }]
        }
        errors = module.validate(bad)
        self.assertTrue(any("source_commit" in error for error in errors))
        self.assertTrue(any("source_blob_sha" in error for error in errors))
        self.assertTrue(any("source_url" in error for error in errors))
        self.assertTrue(any("source_lines" in error for error in errors))


if __name__ == "__main__":
    unittest.main()


class ExternalCorpusRuntimeDiagnosticTests(unittest.TestCase):
    def test_generated_error_context_masks_string_literals(self):
        import importlib.util

        runner = ROOT / "benchmarks" / "run_external_corpus.py"
        spec = importlib.util.spec_from_file_location("external_corpus_runner", runner)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        stderr = (
            'Traceback (most recent call last):\n'
            '  File "/tmp/candidate/translated.py", line 2, in main\n'
            "NameError: name 'cobol_is' is not defined\n"
        )
        generated = "x = 1\nprint('private external output')\n"
        context = module.candidate_error_context(stderr, generated)
        self.assertEqual(context["candidate_error_line_number"], 2)
        self.assertEqual(context["candidate_error_line"], "print(<literal>)")
        self.assertNotIn("private external output", repr(context))


    def test_exception_message_preserves_type_diagnostics_but_masks_data(self):
        import importlib.util

        runner = ROOT / "benchmarks" / "run_external_corpus.py"
        spec = importlib.util.spec_from_file_location("external_corpus_runner_messages", runner)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        message = module.sanitize_exception_message(
            "'str' object does not support item assignment; value='CUSTOM CUSTOMER DATA'"
        )
        self.assertIn("'str' object does not support item assignment", message)
        self.assertNotIn("CUSTOM CUSTOMER DATA", message)
        self.assertIn("<quoted>", message)
