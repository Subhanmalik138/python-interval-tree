"""Command-line interface for the interval tree.

Input format: one interval per line, ``start end [label]`` — numbers may be
ints or floats, the label is free text. Example::

    9 10 standup
    9.5 11 deep-work
    13 14 lunch

Commands:

* ``overlap START END`` — print every stored interval overlapping the query
* ``at POINT`` — print every stored interval containing the point
* ``conflict START END`` — exit 0 if the query overlaps anything, else 1

Intervals are read from a file given with ``-f`` or from stdin.
"""

from __future__ import annotations

import argparse
import sys

from interval_tree import Interval, IntervalTree


def parse_line(line: str) -> Interval:
    parts = line.split()
    if len(parts) < 2:
        raise ValueError(f"expected 'start end [label]', got: {line!r}")
    try:
        start, end = float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise ValueError(f"start/end must be numbers: {line!r}") from exc
    label = " ".join(parts[2:]) or None
    return Interval(start, end, label)


def load_intervals(source) -> IntervalTree:
    tree = IntervalTree()
    for lineno, line in enumerate(source, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tree.insert(parse_line(line))
        except ValueError as exc:
            print(f"line {lineno}: {exc}", file=sys.stderr)
            sys.exit(2)
    return tree


def fmt(interval: Interval) -> str:
    if interval.payload is None:
        return f"{interval.start:g} {interval.end:g}"
    return f"{interval.start:g} {interval.end:g} {interval.payload}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="interval-tree",
        description="Query a set of intervals for overlaps and point containment.",
    )
    parser.add_argument("-f", "--file", help="interval file (default: stdin)")
    sub = parser.add_subparsers(dest="command", required=True)

    overlap = sub.add_parser("overlap", help="list intervals overlapping [start, end)")
    overlap.add_argument("start", type=float)
    overlap.add_argument("end", type=float)

    at = sub.add_parser("at", help="list intervals containing a point")
    at.add_argument("point", type=float)

    conflict = sub.add_parser(
        "conflict", help="exit 0 if [start, end) overlaps anything, else 1"
    )
    conflict.add_argument("start", type=float)
    conflict.add_argument("end", type=float)

    args = parser.parse_args(argv)
    source = open(args.file) if args.file else sys.stdin
    with source:
        tree = load_intervals(source)

    if args.command == "overlap":
        for interval in tree.find_overlapping(Interval(args.start, args.end)):
            print(fmt(interval))
    elif args.command == "at":
        for interval in tree.find_containing(args.point):
            print(fmt(interval))
    elif args.command == "conflict":
        return 0 if tree.has_conflict(Interval(args.start, args.end)) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
