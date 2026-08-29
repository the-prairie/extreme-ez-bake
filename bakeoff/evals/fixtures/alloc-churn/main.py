"""Deliberately allocation-heavy record encoder used by the bakeoff."""

import sys

SAMPLE = (3, 10, 255, 1024, 65535)


def encode(values: tuple[int, ...] | list[int]) -> bytes:
    chunks: list[bytes] = []
    for index, value in enumerate(values):
        record = {  # planted bottleneck: new dict and field list for every item
            "index": index,
            "value": value,
            "checksum": (value + index * 31) & 0xFF,
        }
        fields = [str(record["index"]), str(record["value"]), f'{record["checksum"]:02x}']
        chunks.append(("|".join(fields) + "\n").encode("ascii"))
    return b"".join(chunks)


if __name__ == "__main__":
    if "--golden" not in sys.argv:
        raise SystemExit("usage: python main.py --golden")
    sys.stdout.buffer.write(encode(SAMPLE))
