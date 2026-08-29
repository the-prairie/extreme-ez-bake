"""Deliberately branch-heavy byte classifier used by the bakeoff."""

import sys

CORPUS = b"Az09 \t\n\r{}[]():,.'\"+-*/%=<>!&|^~_@#?;\\\x00\xff"


def classify_byte(value: int) -> int:
    if value == 32: return ord("W")
    elif value == 9: return ord("W")
    elif value == 10: return ord("W")
    elif value == 13: return ord("W")
    elif 48 <= value <= 57: return ord("D")
    elif 65 <= value <= 90: return ord("A")
    elif 97 <= value <= 122: return ord("A")
    elif value == 34: return ord("Q")
    elif value == 39: return ord("Q")
    elif value == 123: return ord("S")
    elif value == 125: return ord("S")
    elif value == 91: return ord("S")
    elif value == 93: return ord("S")
    elif value == 40: return ord("S")
    elif value == 41: return ord("S")
    elif value == 58: return ord("S")
    elif value == 44: return ord("S")
    elif value == 43: return ord("P")
    elif value == 45: return ord("P")
    elif value == 42: return ord("P")
    elif value == 47: return ord("P")
    elif value == 37: return ord("P")
    elif value == 61: return ord("P")
    elif value == 60: return ord("P")
    elif value == 62: return ord("P")
    elif value == 33: return ord("P")
    elif value == 38: return ord("P")
    elif value == 124: return ord("P")
    elif value == 94: return ord("P")
    elif value == 126: return ord("P")
    elif value in (46, 95, 64, 35, 63, 59, 92): return ord("P")
    return ord("X")


def classify(data: bytes) -> bytes:
    return bytes(classify_byte(value) for value in data)


def render_golden() -> bytes:
    return CORPUS.hex().encode("ascii") + b"\n" + classify(CORPUS) + b"\n"


if __name__ == "__main__":
    if "--golden" not in sys.argv:
        raise SystemExit("usage: python main.py --golden")
    sys.stdout.buffer.write(render_golden())
