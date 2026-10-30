"""Regression tests for bounded process capture in the external benchmark."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from run_external_corpus import (\n    MAX_CAPTURE_BYTES, first_byte_difference, preserve_exclusion_diagnostics,\n    run_process, stdout_matches,\n)


class ExternalBenchmarkProcessTests(unittest.TestCase):
    def test_large_stdout_is_capped_and_flagged_without_blocking_child(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process(
                [sys.executable, "-c", "import sys; sys.stdout.write('x' * 3000000)"],
                Path(directory),
                timeout=5,
            )

        self.assertTrue(result["launched"])
        self.assertFalse(result["timeout"])
        self.assertTrue(result["stdout_truncated"])
        self.assertEqual(len(result["stdout"].encode("utf-8")), MAX_CAPTURE_BYTES)
        self.assertEqual(result["stdout_length"], 3000000)
        self.assertEqual(len(result["stdout_sha256"]), 64)

    def test_digest_compares_bytes_beyond_the_retained_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run_process(
                [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000 + 'a')"],
                Path(directory),
                timeout=5,
            )
            second = run_process(
                [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000 + 'b')"],
                Path(directory),
                timeout=5,
            )

        self.assertTrue(first["stdout_truncated"])
        self.assertTrue(second["stdout_truncated"])
        self.assertEqual(first["stdout"], second["stdout"])
        self.assertFalse(stdout_matches(first, second))

    def test_large_stderr_is_capped_and_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process(
                [sys.executable, "-c", "import sys; sys.stderr.write('e' * 3000000)"],
                Path(directory),
                timeout=5,
            )

        self.assertFalse(result["timeout"])
        self.assertTrue(result["stderr_truncated"])
        self.assertEqual(len(result["stderr"].encode("utf-8")), MAX_CAPTURE_BYTES)

    def test_full_streams_are_written_and_first_difference_is_byte_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stdout_path = root / "stdout.bin"
            stderr_path = root / "stderr.bin"
            payload = b"prefix-" + bytes(range(256)) * 5000
            result = run_process(
                [sys.executable, "-c",
                 "import sys; sys.stdout.buffer.write(" + repr(payload) + "); sys.stderr.buffer.write(b'err\\x00')"],
                root, timeout=5, stdout_path=stdout_path, stderr_path=stderr_path,
            )
            self.assertFalse(result["timeout"])
            self.assertEqual(stdout_path.read_bytes(), payload)
            self.assertEqual(stderr_path.read_bytes(), b"err\\x00")
            same_path = root / "same.bin"
            same_path.write_bytes(payload)
            self.assertIsNone(first_byte_difference(stdout_path, same_path))
            changed_path = root / "changed.bin"
            changed_path.write_bytes(payload[:-1] + b"!")
            self.assertEqual(first_byte_difference(stdout_path, changed_path), len(payload) - 1)

    def test_reference_exclusion_bundle_is_complete_and_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_root = root / "output"
            case_root = root / "case"
            case_root.mkdir()
            source = root / "program.cbl"
            source.write_text("IDENTIFICATION DIVISION.\\n", encoding="utf-8")
            (case_root / "reference-compile.stdout.bin").write_bytes(b"compile out")
            (case_root / "reference-compile.stderr.bin").write_bytes(b"compile err")
            (case_root / "reference.stdout.bin").write_bytes(b"runtime out")
            (case_root / "reference.stderr.bin").write_bytes(b"runtime err")
            result = {
                "id": "fixture-123", "status": "excluded",
                "reason": "reference execution timed out",
            }
            compiled = {"returncode": 0}
            preserve_exclusion_diagnostics(output_root, case_root, source, result, compiled)
            bundle = output_root / "diagnostics" / "fixture-123"
            self.assertEqual((bundle / "source.cbl").read_text(encoding="utf-8"),
                             "IDENTIFICATION DIVISION.\\n")
            self.assertEqual((bundle / "reference.stdout.bin").read_bytes(), b"runtime out")
            metadata_text = (bundle / "metadata.json").read_text(encoding="utf-8")
            self.assertTrue(metadata_text.endswith("\\n"))
            import json
            metadata = json.loads(metadata_text)
            self.assertIn("reference exclusion", metadata["classification"])
            self.assertIn("not counted", metadata["classification"])
            self.assertEqual(metadata["reference_compile_returncode"], 0)

    def test_timeout_still_kills_a_running_process(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_process(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                Path(directory),
                timeout=1,
            )

        self.assertTrue(result["timeout"])
        self.assertNotEqual(result["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
