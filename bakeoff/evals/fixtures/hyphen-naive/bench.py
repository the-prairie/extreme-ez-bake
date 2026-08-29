import json
import math
import statistics
import time

from main import FIXED_WORDS, hyphenation_points

WORDS = (FIXED_WORDS * 500)[:5000]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> None:
    samples = []
    checksum = 0
    for _ in range(9):
        started = time.perf_counter()
        for word in WORDS:
            checksum += len(hyphenation_points(word))
        samples.append((time.perf_counter() - started) * 1000)
    assert checksum > 0
    print(json.dumps({
        "scenario": "hyphen-naive",
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
