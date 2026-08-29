import unittest

from main import SAMPLE, encode


class AllocChurnTests(unittest.TestCase):
    def test_exact_output_bytes(self) -> None:
        expected = b"0|3|03\n1|10|29\n2|255|3d\n3|1024|5d\n4|65535|7b\n"
        self.assertEqual(encode(SAMPLE), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(encode([]), b"")

    def test_golden_bytes_are_stable(self) -> None:
        with open("golden.txt", "rb") as handle:
            self.assertEqual(encode(SAMPLE), handle.read())


if __name__ == "__main__":
    unittest.main()
