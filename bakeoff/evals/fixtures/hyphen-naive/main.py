"""Deliberately naive pattern-scanning hyphenator used by the bakeoff."""

import sys

PATTERNS = [
    ("hy", 2), ("phen", 4), ("op", 2), ("ti", 2), ("mi", 2), ("za", 2),
    ("cro", 3), ("ser", 3), ("vice", 4), ("al", 2), ("go", 2), ("rithm", 5),
    ("look", 4), ("up", 2), ("ta", 2), ("ble", 3), ("pre", 3), ("com", 3),
    ("pute", 4), ("buf", 3), ("fer", 3), ("size", 4), ("ze", 2), ("ro", 2),
    ("co", 2), ("py", 2), ("pro", 3), ("fil", 3), ("ing", 3), ("branch", 6),
    ("less", 4), ("amber", 3), ("baker", 2), ("cider", 3), ("delta", 2),
    ("ember", 3), ("fable", 2), ("gamut", 3), ("hazel", 2), ("ivory", 3),
    ("jolly", 2), ("karma", 3), ("lemon", 2), ("mango", 3), ("navy", 2),
    ("olive", 3), ("pearl", 2), ("quill", 3), ("raven", 2), ("solar", 3),
    ("tango", 2), ("umber", 3), ("vivid", 2), ("waltz", 3), ("xenon", 2),
    ("yodel", 3), ("zebra", 2), ("cobalt", 3), ("fjord", 2), ("glyph", 3),
]

FIXED_WORDS = (
    "hyphenation", "optimization", "microservice", "algorithm", "lookuptable",
    "precompute", "bufferpresize", "zerocopy", "profiling", "branchless",
)


def hyphenation_points(word: str) -> tuple[int, ...]:
    points: set[int] = set()
    for pattern, offset in PATTERNS:  # planted bottleneck: scan every pattern per word
        start = 0
        while (index := word.find(pattern, start)) != -1:
            point = index + offset
            if 0 < point < len(word):
                points.add(point)
            start = index + 1
    return tuple(sorted(points))


def render(words: tuple[str, ...] = FIXED_WORDS) -> str:
    return "".join(f"{word}:{','.join(map(str, hyphenation_points(word)))}\n" for word in words)


if __name__ == "__main__":
    if "--golden" not in sys.argv:
        raise SystemExit("usage: python main.py --golden")
    sys.stdout.write(render())
