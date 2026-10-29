"""Tests for Interval and IntervalTree, including a brute-force cross-check."""

import random

import pytest

from interval_tree import Interval, IntervalTree


def brute_overlaps(intervals, query):
    return sorted(i for i in intervals if i.overlaps(query))


def brute_containing(intervals, point):
    return sorted(i for i in intervals if i.contains_point(point))


def test_empty_tree():
    tree = IntervalTree()
    assert len(tree) == 0
    assert tree.find_overlapping(Interval(0, 10)) == []
    assert tree.find_containing(5) == []
    assert not tree.has_conflict(Interval(0, 10))
    assert list(tree) == []


def test_interval_validation():
    with pytest.raises(ValueError):
        Interval(5, 5)
    with pytest.raises(ValueError):
        Interval(8, 2)


def test_touching_endpoints_do_not_overlap():
    tree = IntervalTree([Interval(1, 3, "a"), Interval(3, 5, "b")])
    assert tree.find_overlapping(Interval(3, 4)) == [Interval(3, 5, "b")]
    assert tree.find_containing(3) == [Interval(3, 5, "b")]


def test_overlap_query_and_order():
    intervals = [Interval(0, 5, "a"), Interval(3, 8, "b"), Interval(10, 12, "c")]
    tree = IntervalTree(intervals)
    assert tree.find_overlapping(Interval(4, 11)) == [
        Interval(0, 5, "a"),
        Interval(3, 8, "b"),
        Interval(10, 12, "c"),
    ]
    assert tree.find_overlapping(Interval(6, 9)) == [Interval(3, 8, "b")]


def test_stabbing_query():
    tree = IntervalTree(
        [Interval(0, 10, "wide"), Interval(2, 4, "narrow"), Interval(6, 9, "late")]
    )
    assert tree.find_containing(3) == [Interval(0, 10, "wide"), Interval(2, 4, "narrow")]
    assert tree.find_containing(10) == []  # half-open: end is exclusive


def test_has_conflict_short_circuits():
    tree = IntervalTree([Interval(0, 5, "a")])
    assert tree.has_conflict(Interval(4, 6))
    assert not tree.has_conflict(Interval(5, 6))


def test_insert_remove_and_contains():
    tree = IntervalTree()
    a, b = Interval(1, 4, "a"), Interval(2, 6, "b")
    tree.insert(a)
    tree.insert(b)
    assert len(tree) == 2
    assert a in tree and b in tree
    assert tree.remove(a)
    assert a not in tree and len(tree) == 1
    assert not tree.remove(a)  # already gone
    assert tree.find_overlapping(Interval(0, 10)) == [b]


def test_remove_node_with_two_children():
    tree = IntervalTree.from_intervals(
        [Interval(5, 6, "root"), Interval(2, 3, "l"), Interval(8, 9, "r"),
         Interval(1, 2, "ll"), Interval(3, 4, "lr")]
    )
    assert tree.remove(Interval(5, 6, "root"))
    assert list(tree) == [
        Interval(1, 2, "ll"),
        Interval(2, 3, "l"),
        Interval(3, 4, "lr"),
        Interval(8, 9, "r"),
    ]
    assert tree.find_overlapping(Interval(0, 10)) == list(tree)


def test_iteration_is_sorted():
    intervals = [Interval(5, 6), Interval(1, 2), Interval(3, 4)]
    assert list(IntervalTree(intervals)) == sorted(intervals)


def test_from_intervals_balanced():
    tree = IntervalTree.from_intervals(Interval(i, i + 1) for i in range(100))
    assert len(tree) == 100
    assert tree.find_containing(42) == [Interval(42, 43)]


def test_random_against_brute_force():
    rng = random.Random(42)
    intervals = []
    for i in range(200):
        start = rng.randint(0, 100)
        intervals.append(Interval(start, start + rng.randint(1, 20), f"i{i}"))
    tree = IntervalTree(intervals)
    for _ in range(200):
        start = rng.randint(0, 100)
        query = Interval(start, start + rng.randint(1, 20))
        assert tree.find_overlapping(query) == brute_overlaps(intervals, query)
        point = rng.randint(0, 120)
        assert tree.find_containing(point) == brute_containing(intervals, point)


def test_random_removals_stay_consistent():
    rng = random.Random(7)
    intervals = [Interval(i, i + rng.randint(1, 5), f"i{i}") for i in range(50)]
    tree = IntervalTree(intervals)
    remaining = list(intervals)
    for interval in rng.sample(intervals, 25):
        assert tree.remove(interval)
        remaining.remove(interval)
    assert list(tree) == sorted(remaining)
    assert tree.find_overlapping(Interval(0, 100)) == sorted(remaining)
