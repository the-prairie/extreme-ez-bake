import unittest

from main import CORPUS, classify, classify_byte, render_golden


class ParseBranchyTests(unittest.TestCase):
    def test_fixed_corpus(self) -> None:
        expected = b"AADDWWWWSSSSSSSSPQQPPPPPPPPPPPPPPPPPPPXX"
        self.assertEqual(classify(CORPUS), expected)

    def test_representative_classes(self) -> None:
        self.assertEqual(classify_byte(ord("7")), ord("D"))
        self.assertEqual(classify_byte(ord("q")), ord("A"))
        self.assertEqual(classify_byte(0), ord("X"))

    def test_golden_bytes_are_stable(self) -> None:
        with open("golden.txt", "rb") as handle:
            self.assertEqual(render_golden(), handle.read())


if __name__ == "__main__":
    unittest.main()
