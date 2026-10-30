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
            payload = b"prefix-" + bytes(range(256)) * 20
            code = "import sys; sys.stdout.buffer.write(b'prefix-' + bytes(range(256)) * 20); sys.stderr.buffer.write(bytes([101,114,114,0]))"
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

    def test_launch_failure_still_creates_empty_diagnostic_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out, err = root / "nested" / "stdout.bin", root / "nested" / "stderr.bin"
            result = run_process([str(root / "does-not-exist")], root, 2, out, err)
            self.assertFalse(result["launched"])
            self.assertEqual(out.read_bytes(), b"")
            self.assertEqual(err.read_bytes(), b"")
            reference = root / "reference.bin"
            reference.write_bytes(b"reference output")
            self.assertEqual(first_byte_difference(out, reference), 0)


    def test_main_end_to_end_diagnostic_bundles_and_denominator(self):
        import contextlib
        import hashlib
        import io
        import json
        import sys
        from unittest import mock
        import run_external_corpus as runner

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive.zip"
            archive.write_bytes(b"mock archive")
            translator = root / "translator.py"
            translator.write_text("# mock translator", encoding="utf-8")
            output = root / "output"
            source_names = [
                "case-a.cbl", "case-b.cbl", "case-c.cbl",
                "case-d.cbl", "case-e.cbl", "case-f.cbl", "case-g.cbl",
            ]
            compile_index = [0]
            eligible_index = [0]

            def fake_extract(_archive, destination):
                destination.mkdir(parents=True, exist_ok=True)
                sources = []
                for name in source_names:
                    source = destination / name
                    source.write_text(f"IDENTIFICATION DIVISION. *> {name}\n", encoding="utf-8")
                    sources.append(source)
                return sources

            def result(stdout=b"", stderr=b"", returncode=0, timeout=False,
                       launched=True, stdout_path=None, stderr_path=None):
                if stdout_path is not None:
                    stdout_path.parent.mkdir(parents=True, exist_ok=True)
                    stdout_path.write_bytes(stdout)
                if stderr_path is not None:
                    stderr_path.parent.mkdir(parents=True, exist_ok=True)
                    stderr_path.write_bytes(stderr)
                return {
                    "launched": launched, "returncode": returncode,
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "timeout": timeout, "stdout_truncated": False,
                    "stderr_truncated": False,
                    "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                    "stdout_length": len(stdout),
                }

            def fake_run_process(command, _cwd, _timeout, stdout_path=None, stderr_path=None):
                if command[0] == "cobc":
                    compile_index[0] += 1
                    if compile_index[0] == 1:
                        return result(stderr=b"fixture compile error\n", returncode=1,
                                      stdout_path=stdout_path, stderr_path=stderr_path)
                    return result(stdout_path=stdout_path, stderr_path=stderr_path)
                if str(command[0]).endswith("/reference"):
                    if compile_index[0] == 2:
                        return result(stderr=b"reference timeout\n", timeout=True,
                                      stdout_path=stdout_path, stderr_path=stderr_path)
                    return result(stdout=b"reference\n", stdout_path=stdout_path,
                                  stderr_path=stderr_path)
                if command[0] == "python3" and "--format" in command:
                    eligible_index[0] += 1
                    if eligible_index[0] == 1:
                        return result(stderr=b"translator failed\n", returncode=2,
                                      stdout_path=stdout_path, stderr_path=stderr_path)
                    if eligible_index[0] == 2:
                        return result(stdout=b"def broken(:\n", stdout_path=stdout_path,
                                      stderr_path=stderr_path)
                    if eligible_index[0] == 3:
                        return result(stdout=b"print('candidate')\n", stdout_path=stdout_path,
                                      stderr_path=stderr_path)
                    if eligible_index[0] == 4:
                        return result(stdout=b"print('launch-failure')\n", stdout_path=stdout_path,
                                      stderr_path=stderr_path)
                    return result(stdout=b"print('same')\n", stdout_path=stdout_path,
                                  stderr_path=stderr_path)
                if command[0] == "python3":
                    if eligible_index[0] == 4:
                        return result(stderr=b"FileNotFoundError: executable missing",
                                      launched=False, stdout_path=stdout_path,
                                      stderr_path=stderr_path)
                    payload = b"candidate\n" if eligible_index[0] == 3 else b"reference\n"
                    return result(stdout=payload, stdout_path=stdout_path, stderr_path=stderr_path)
                raise AssertionError(f"unexpected command: {command!r}")

            argv = [
                "run_external_corpus.py", "--archive", str(archive),
                "--translator", str(translator), "--output", str(output),
                "--target", "5", "--diagnostics",
            ]
            stdout = io.StringIO()
            with mock.patch.object(runner, "extract_archive", side_effect=fake_extract), \
                 mock.patch.object(runner, "run_process", side_effect=fake_run_process), \
                 mock.patch.object(sys, "argv", argv), \
                 contextlib.redirect_stdout(stdout):
                self.assertEqual(runner.main(), 0)

            report = json.loads((output / "external-corpus-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["reference_compile_failures"], 1)
            self.assertEqual(report["reference_runtime_exclusions"], 1)
            self.assertEqual(report["tested"], 5)
            self.assertEqual(report["passed"], 1)
            self.assertEqual(report["failed"], 4)
            self.assertTrue(report["sample_complete"])
            self.assertEqual(len(report["results"]), 5)
            self.assertEqual(report["eligible_skipped"], 0)

            bundles = list((output / "diagnostics").iterdir())
            self.assertEqual(len(bundles), 6)  # 2 reference exclusions + 4 candidate failures
            metadata = {
                item.name: json.loads((item / "metadata.json").read_text(encoding="utf-8"))
                for item in bundles
            }
            exclusions = [item for item in metadata.values()
                          if "reference exclusion" in item.get("classification", "")]
            self.assertEqual(len(exclusions), 2)
            self.assertTrue(all("not counted" in item["classification"] for item in exclusions))

            mismatch = next(item["case"] for item in metadata.values()
                            if item["case"].get("stdout_match") is False)
            self.assertEqual(mismatch["stdout_first_difference_byte"], 0)
            mismatch_dir = output / "diagnostics" / mismatch["id"]
            for name in ("source.cbl", "translated.py", "reference.stdout.bin",
                         "candidate.stdout.bin", "reference.stderr.bin",
                         "candidate.stderr.bin", "metadata.json"):
                self.assertTrue((mismatch_dir / name).is_file(), name)

            syntax_case = next(item for item in report["results"]
                               if "generated Python syntax error" in (item.get("reason") or ""))
            syntax_dir = output / "diagnostics" / syntax_case["id"]
            self.assertTrue((syntax_dir / "translated.py").is_file())
            self.assertTrue((syntax_dir / "translator.stdout.bin").is_file())
            self.assertFalse((syntax_dir / "candidate.stdout.bin").exists())

            launch_case = next(item for item in report["results"]
                               if item.get("reason") == "translated program could not launch")
            self.assertFalse(launch_case["candidate_launched"])
            launch_dir = output / "diagnostics" / launch_case["id"]
            launch_metadata = json.loads((launch_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertFalse(launch_metadata["candidate_launched"])
            self.assertTrue((launch_dir / "candidate.stderr.bin").is_file())

            translator_failure = next(item for item in report["results"]
                                      if (item.get("reason") or "").strip() == "translator failed")
            translator_dir = output / "diagnostics" / translator_failure["id"]
            self.assertTrue((translator_dir / "source.cbl").is_file())
            self.assertTrue((translator_dir / "translator.stderr.bin").is_file())

if __name__ == "__main__": unittest.main()

