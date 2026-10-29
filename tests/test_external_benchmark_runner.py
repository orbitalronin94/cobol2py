"""Regression tests for bounded process capture in the external benchmark."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from run_external_corpus import MAX_CAPTURE_BYTES, run_process


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
