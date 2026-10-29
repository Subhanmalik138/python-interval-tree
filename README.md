# Interval Tree

A small, dependency-free interval tree in Python: store a set of time ranges
(or any numeric ranges) and answer two questions fast — *which intervals
overlap this one?* and *which intervals contain this point?*

Useful wherever ranges collide: calendar conflict detection, booking
systems, genomic feature lookup, memory-allocation maps.

## Problem

A naive overlap search scans every stored interval — O(n) per query. An
interval tree answers the same query in O(log n + k) average time, where k
is the number of matches, by pruning whole subtrees that cannot overlap.

## Design decisions

1. **Augmented BST keyed on start, with `max_end` per node.** Each node
   stores the largest end value in its subtree. During an overlap search,
   a left subtree whose `max_end <= query.start` is skipped entirely —
   that single value is what turns a linear scan into a logarithmic one.
2. **Half-open intervals `[start, end)`.** Touching endpoints do not
   count as overlapping (`[1, 3)` and `[3, 5)` are conflict-free). This
   matches how bookings and schedules behave and removes a whole class
   of off-by-one bugs.
3. **Balanced build for sorted input.** Plain insertion degrades on
   pre-sorted data, so `IntervalTree.from_intervals` inserts in
   median-first order, keeping depth near log n without a full
   self-balancing implementation.
4. **Payloads are data, not keys.** Intervals sort and compare on
   endpoints only, so any hashable payload (a meeting name, a record id)
   can ride along without breaking ordering.

## Usage

```python
from interval_tree import Interval, IntervalTree

tree = IntervalTree([
    Interval(9, 10, "standup"),
    Interval(9.5, 11, "deep work"),
    Interval(13, 14, "lunch"),
])

tree.find_overlapping(Interval(9.75, 10.5))
# [Interval(9, 10, 'standup'), Interval(9.5, 11, 'deep work')]

tree.find_containing(13.5)
# [Interval(13, 14, 'lunch')]

tree.has_conflict(Interval(10, 11))  # True — overlaps "deep work"
tree.remove(Interval(9, 10, "standup"))
```

## CLI

```bash
pip install .
interval-tree -f schedule.txt overlap 9.75 10.5
interval-tree -f schedule.txt at 13.5
interval-tree -f schedule.txt conflict 10 11; echo $?   # 0 = conflict
```

Input file format — one interval per line, `start end [label]`:

```
9 10 standup
9.5 11 deep work
13 14 lunch
```

## Running tests

```bash
pip install pytest
pytest
```

The suite covers overlap/stabbing edge cases (touching endpoints,
half-open end), removal of two-child nodes, and randomized cross-checks
against a brute-force scan.

## Tech stack

Python 3.9+ standard library only. No dependencies.
