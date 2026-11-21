"""CLI: python -m generator --size s --out data/s --seed 42"""

import argparse
import sys
import time
from pathlib import Path

from .generate import SIZES, generate
from .writers import MongoWriter, Neo4jWriter, RelationalWriter


def build_writers(out):
    return [RelationalWriter(out / "relational"), MongoWriter(out / "mongo"), Neo4jWriter(out / "neo4j")]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m generator", description=__doc__)
    parser.add_argument("--size", choices=SIZES, required=True,
                        help="rows in order_items: s=10k, m=500k, l=1M, xl=10M")
    parser.add_argument("--out", type=Path, help="output directory (default: data/<size>)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quiet", action="store_true", help="hide progress output")
    args = parser.parse_args(argv)

    out = args.out or Path("data") / args.size
    print(f"Generating size {args.size} ({SIZES[args.size]:,} order items) into {out}", file=sys.stderr)
    start = time.perf_counter()
    counts = generate(SIZES[args.size], args.seed, build_writers(out), progress=not args.quiet)
    print(f"Done in {time.perf_counter() - start:.1f}s: "
          + ", ".join(f"{k}={v:,}" for k, v in counts.items()), file=sys.stderr)


if __name__ == "__main__":
    main()
