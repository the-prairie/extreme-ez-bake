import unittest

from main import FIXED_WORDS, hyphenation_points, render


class HyphenNaiveTests(unittest.TestCase):
    def test_fixed_points(self) -> None:
        expected = {
            "hyphenation": (2, 6, 9),
            "optimization": (2, 4, 6, 8, 10),
            "microservice": (2, 5, 8),
            "algorithm": (2, 4),
            "lookuptable": (4, 6, 8),
            "precompute": (3, 5, 6),
            "bufferpresize": (3, 6, 9),
            "zerocopy": (2, 4, 6, 7),
            "profiling": (3, 6),
            "branchless": (6,),
        }
        self.assertEqual({word: hyphenation_points(word) for word in FIXED_WORDS}, expected)

    def test_golden_render_is_stable(self) -> None:
        with open("golden.txt", encoding="utf-8") as handle:
            self.assertEqual(render(), handle.read())


if __name__ == "__main__":
    unittest.main()
