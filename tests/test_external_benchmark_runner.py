"""Regression tests for bounded process capture in the external benchmark."""
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from run_external_corpus import MAX_CAPTURE_BYTES, run_process, stdout_matches, first_byte_difference, preserve_exclusion_diagnostics

class ExternalBenchmarkProcessTests(unittest.TestCase):
    def test_large_stdout_is_capped_and_flagged_without_blocking_child(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process([sys.executable, "-c", "import sys; sys.stdout.write('x' * 3000000)"], Path(directory), 5)
        self.assertTrue(result["launched"]); self.assertFalse(result["timeout"]); self.assertTrue(result["stdout_truncated"])
        self.assertEqual(len(result["stdout"].encode("utf-8")), MAX_CAPTURE_BYTES)
        self.assertEqual(result["stdout_length"], 3000000); self.assertEqual(len(result["stdout_sha256"]), 64)

    def test_digest_compares_bytes_beyond_retained_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run_process([sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000 + 'a')"], Path(directory), 5)
            second = run_process([sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000 + 'b')"], Path(directory), 5)
        self.assertTrue(first["stdout_truncated"]); self.assertTrue(second["stdout_truncated"])
        self.assertEqual(first["stdout"], second["stdout"]); self.assertFalse(stdout_matches(first, second))

    def test_large_stderr_is_capped_and_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process([sys.executable, "-c", "import sys; sys.stderr.write('e' * 3000000)"], Path(directory), 5)
        self.assertFalse(result["timeout"]); self.assertTrue(result["stderr_truncated"])
        self.assertEqual(len(result["stderr"].encode("utf-8")), MAX_CAPTURE_BYTES)

    def test_timeout_still_kills_running_process(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process([sys.executable, "-c", "import time; time.sleep(10)"], Path(directory), 1)
        self.assertTrue(result["timeout"]); self.assertNotEqual(result["returncode"], 0)

    def test_full_stream_files_and_byte_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / "stdout.bin"; err = root / "stderr.bin"
            payload = b"prefix-" + bytes(range(256)) * 5000
            code = "import sys; sys.stdout.buffer.write(" + repr(payload) + "); sys.stderr.buffer.write(bytes([101,114,114,0]))"
            result = run_process([sys.executable, "-c", code], root, 5, out, err)
            self.assertFalse(result["timeout"]); self.assertEqual(out.read_bytes(), payload)
            self.assertEqual(err.read_bytes(), bytes([101,114,114,0]))
            same = root / "same.bin"; same.write_bytes(payload)
            self.assertIsNone(first_byte_difference(out, same))
            changed = root / "changed.bin"; changed.write_bytes(payload[:-1] + b"!")
            self.assertEqual(first_byte_difference(out, changed), len(payload)-1)

    def test_reference_exclusion_bundle_contains_evidence_and_valid_metadata(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root / "output"; case = root / "case"; case.mkdir()
            source = root / "fixture.cbl"; source.write_text("IDENTIFICATION DIVISION.", encoding="utf-8")
            for name in ("reference-compile.stdout.bin", "reference-compile.stderr.bin", "reference.stdout.bin", "reference.stderr.bin"):
                (case / name).write_bytes(name.encode("ascii"))
            result = {"id": "fixture-123", "status": "excluded", "reason": "reference timeout"}
            preserve_exclusion_diagnostics(output, case, source, result, {"returncode": 0})
            bundle = output / "diagnostics" / "fixture-123"
            self.assertEqual((bundle / "source.cbl").read_text(encoding="utf-8"), "IDENTIFICATION DIVISION.")
            self.assertEqual((bundle / "reference.stdout.bin").read_bytes(), b"reference.stdout.bin")
            raw = (bundle / "metadata.json").read_text(encoding="utf-8")
            self.assertTrue(raw.endswith(chr(10))); metadata = json.loads(raw)
            self.assertIn("reference exclusion", metadata["classification"])
            self.assertIn("not counted", metadata["classification"])
            self.assertEqual(metadata["reference_compile_returncode"], 0)

if __name__ == "__main__": unittest.main()

