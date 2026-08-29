import json
import math
import statistics
import time

from main import CORPUS, classify

SIZE = 2 * 1024 * 1024
DATA = (CORPUS * (SIZE // len(CORPUS) + 1))[:SIZE]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> None:
    samples = []
    checksum = 0
    for _ in range(3):
        started = time.perf_counter()
        checksum ^= classify(DATA)[-1]
        samples.append((time.perf_counter() - started) * 1000)
    assert checksum >= 0
    print(json.dumps({
        "scenario": "parse-branchy",
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
