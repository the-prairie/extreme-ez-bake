# alloc-churn

This deterministic fixture encodes records while allocating a dictionary, a field list, a string, and a bytes object for every item. The planted bottleneck is per-item allocation churn; the expected hotspot class is **alloc / arena**.

`python -m unittest discover -s . -p 'test_*.py'` pins exact output bytes. `python bench.py` reports timing JSON and explicitly notes allocation pressure. `python main.py --golden` must remain byte-for-byte equal to `golden.txt`.
