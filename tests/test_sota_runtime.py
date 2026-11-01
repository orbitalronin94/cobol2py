import unittest
from decimal import Decimal

from ronin.runtime_adapters import CobolDecimal, CobolOverflowError, CobolString, GroupView
from ronin.copybook_parser import parse_pic_string, denormalize_occurs, handle_redefines


class RuntimeAdapterTests(unittest.TestCase):
    def test_decimal_truncates_instead_of_rounding(self):
        self.assertEqual(str(CobolDecimal("1.999", scale=2)), "1.99")

    def test_decimal_rounded_mode_and_overflow(self):
        self.assertEqual(str(CobolDecimal("1.999", scale=2, rounded=True)), "2.00")
        with self.assertRaises(CobolOverflowError):
            CobolDecimal("100", scale=0, digits=2)

    def test_fixed_string_pads_truncates_and_has_ebcdic_key(self):
        value = CobolString("ABCDE", 3)
        self.assertEqual(str(value), "ABC")
        self.assertEqual(str(CobolString("A", 3)), "A  ")
        self.assertEqual(value.collating_key(), b"\xc1\xc2\xc3")

    def test_group_views_share_mutable_storage(self):
        storage = bytearray(b"ABCD")
        left = GroupView(storage, 0, 4, {"first": (0, 2), "last": (2, 2)})
        right = GroupView(storage, 1, 2)
        left.write("last", b"XY")
        self.assertEqual(right.bytes(), b"BX")
        left.move_from(b"Q")
        self.assertEqual(storage, bytearray(b"Q   "))


class CopybookMetadataTests(unittest.TestCase):
    def test_pic_decimal_metadata(self):
        pic = parse_pic_string("S9(5)V99 COMP-3")
        self.assertEqual((pic.category, pic.length, pic.precision, pic.scale, pic.signed, pic.usage),
                         ("numeric", 7, 7, 2, True, "COMP-3"))

    def test_occurs_and_redefines_are_explicit(self):
        lines = ["01 BASE PIC X(4).", "01 VIEW REDEFINES BASE PIC 9(4).",
                 "05 ITEM PIC X(2) OCCURS 3 TIMES."]
        entries = denormalize_occurs(lines)
        items = [entry for entry in entries if entry["source_name"] == "ITEM"]
        self.assertEqual([item["name"] for item in items], ["ITEM-1", "ITEM-2", "ITEM-3"])
        overlay = next(entry for entry in handle_redefines(lines) if entry["source_name"] == "VIEW")
        self.assertTrue(overlay["overlay_target_found"])
        self.assertFalse(overlay["offsets_resolved"])


if __name__ == "__main__":
    unittest.main()
