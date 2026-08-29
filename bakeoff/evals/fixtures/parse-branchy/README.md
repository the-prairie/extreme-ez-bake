# parse-branchy

This deterministic fixture classifies each byte through a long `if`/`elif` decision chain. The planted bottleneck is branch-heavy byte classification; the expected hotspot class is **branch / lookup-table**.

`python -m unittest discover -s . -p 'test_*.py'` pins a fixed byte corpus. `python bench.py` classifies exactly 2 MiB and prints JSON timing data. `python main.py --golden` must remain byte-for-byte equal to `golden.txt`.
