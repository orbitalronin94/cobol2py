"""Tests for privacy-preserving external benchmark failure classification."""
import unittest

from benchmarks.run_external_multilang import native_rejection_code, safe_reason


class NativeRejectionDiagnosticsTests(unittest.TestCase):
    def test_statement_rejections_have_stable_codes(self):
        self.assertEqual(
            native_rejection_code("cobol2native: statement not supported by experimental c backend: DISPLAY"),
            "unsupported_statement",
        )

    def test_control_flow_rejections_have_stable_codes(self):
        self.assertEqual(
            native_rejection_code("cobol2native: control-flow node 'perform' is not yet supported"),
            "unsupported_control_flow",
        )

    def test_data_layout_rejections_have_stable_codes(self):
        self.assertEqual(
            native_rejection_code("cobol2native: data layout outside native subset (OCCURS and REDEFINES need support)"),
            "unsupported_data_layout",
        )

    def test_conditions_and_pictures_are_distinguished(self):
        self.assertEqual(
            native_rejection_code("cobol2native: IF condition outside native subset"),
            "unsupported_condition",
        )
        self.assertEqual(
            native_rejection_code("cobol2native: unsupported PIC for WS-X"),
            "unsupported_picture",
        )

    def test_unrecognized_rejection_falls_back_to_stable_category(self):
        self.assertEqual(native_rejection_code("cobol2native: unexpected edge case"), "other_native_rejection")

    def test_safe_reason_remains_source_free(self):
        process = {
            "launched": True,
            "timeout": False,
            "stdout_truncated": False,
            "returncode": 2,
            "stderr": "cobol2native: statement not supported by experimental c backend: private field",
        }
        self.assertEqual(
            safe_reason("c", "translation", process),
            "unsupported construct or native translation rejection",
        )


if __name__ == "__main__":
    unittest.main()
