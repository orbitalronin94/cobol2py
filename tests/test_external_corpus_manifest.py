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
                "source_url": "https://github.com/example/bad/blob/main/bad.cob",
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
