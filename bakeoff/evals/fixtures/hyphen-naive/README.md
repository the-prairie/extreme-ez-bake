# hyphen-naive

This deterministic fixture hyphenates a fixed vocabulary by scanning the entire pattern list for every word. The planted bottleneck is the per-word linear pattern scan; the expected hotspot class is **algo / lookup-table / trie**.

`python -m unittest discover -s . -p 'test_*.py'` pins exact break points. `python bench.py` processes exactly 5,000 words and prints JSON timing data. `python main.py --golden` must remain byte-for-byte equal to `golden.txt`.
