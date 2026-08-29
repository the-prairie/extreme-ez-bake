import json
import math
import statistics
import time

from main import encode

VALUES = tuple((index * 2654435761) & 0xFFFF for index in range(50_000))


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> None:
    samples = []
    checksum = 0
    for _ in range(7):
        started = time.perf_counter()
        checksum ^= len(encode(VALUES))
        samples.append((time.perf_counter() - started) * 1000)
    assert checksum > 0
    print(json.dumps({
        "scenario": "alloc-churn",
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
        "note": "per-item list/dict allocation pressure",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
