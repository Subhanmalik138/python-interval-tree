"""An augmented binary search tree for interval queries.

The tree is keyed on interval start. Every node stores ``max_end`` — the
largest end value in its subtree — which is what makes overlap search
fast: when searching for overlaps with ``[s, e)``, a left subtree whose
``max_end <= s`` cannot contain any overlapping interval and is pruned
whole. The same augmentation prunes stabbing (point) queries.

Complexities (n = number of intervals, k = matches returned):

- insert / remove: O(log n) average, O(n) worst case (unbalanced tree)
- overlap search: O(log n + k) average
- stabbing query: O(log n + k) average

The tree is deliberately unbalanced to keep the code small and readable;
for adversarial, pre-sorted input, shuffle before inserting or build via
``IntervalTree.from_intervals`` which inserts in a median-first order.
"""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from .interval import Interval


class _Node:
    __slots__ = ("interval", "max_end", "left", "right")

    def __init__(self, interval: Interval) -> None:
        self.interval = interval
        self.max_end = interval.end
        self.left: Optional[_Node] = None
        self.right: Optional[_Node] = None

    def refresh(self) -> None:
        """Recompute ``max_end`` from this node and its children."""
        self.max_end = self.interval.end
        if self.left is not None:
            self.max_end = max(self.max_end, self.left.max_end)
        if self.right is not None:
            self.max_end = max(self.max_end, self.right.max_end)


class IntervalTree:
    """A mutable set of intervals with fast overlap and point queries."""

    def __init__(self, intervals: Iterable[Interval] = ()) -> None:
        self._root: Optional[_Node] = None
        self._size = 0
        for interval in intervals:
            self.insert(interval)

    # -- construction ---------------------------------------------------

    @classmethod
    def from_intervals(cls, intervals: Iterable[Interval]) -> "IntervalTree":
        """Build a roughly balanced tree by inserting in median-first order.

        Sorting by start and recursing on the median keeps the tree depth
        near log n even for pre-sorted input, at the cost of one sort.
        """
        ordered = sorted(intervals)
        tree = cls()
        tree._build_balanced(ordered)
        return tree

    def _build_balanced(self, ordered: list[Interval]) -> None:
        if not ordered:
            return
        mid = len(ordered) // 2
        self.insert(ordered[mid])
        self._build_balanced(ordered[:mid])
        self._build_balanced(ordered[mid + 1:])

    # -- mutation -------------------------------------------------------

    def insert(self, interval: Interval) -> None:
        """Insert ``interval``. Duplicates (same start, end, payload) are kept."""
        self._root = self._insert(self._root, interval)
        self._size += 1

    def _insert(self, node: Optional[_Node], interval: Interval) -> _Node:
        if node is None:
            return _Node(interval)
        if interval < node.interval:
            node.left = self._insert(node.left, interval)
        else:
            node.right = self._insert(node.right, interval)
        node.refresh()
        return node

    def remove(self, interval: Interval) -> bool:
        """Remove one occurrence of ``interval``. Returns True if removed."""
        self._root, removed = self._remove(self._root, interval)
        if removed:
            self._size -= 1
        return removed

    def _remove(
        self, node: Optional[_Node], interval: Interval
    ) -> tuple[Optional[_Node], bool]:
        if node is None:
            return None, False
        if interval < node.interval:
            node.left, removed = self._remove(node.left, interval)
        elif interval > node.interval:
            node.right, removed = self._remove(node.right, interval)
        else:
            removed = True
            if node.left is None:
                return node.right, True
            if node.right is None:
                return node.left, True
            # Two children: replace with the in-order successor, then
            # delete the successor from the right subtree.
            successor = node.right
            while successor.left is not None:
                successor = successor.left
            node.interval = successor.interval
            node.right, _ = self._remove(node.right, successor.interval)
        node.refresh()
        return node, removed

    # -- queries --------------------------------------------------------

    def find_overlapping(self, query: Interval) -> list[Interval]:
        """All stored intervals overlapping ``query``, in start order."""
        found: list[Interval] = []
        self._search_overlap(self._root, query, found)
        return found

    def _search_overlap(
        self, node: Optional[_Node], query: Interval, found: list[Interval]
    ) -> None:
        if node is None:
            return
        # Prune the left subtree: nothing in it ends after query.start.
        if node.left is not None and node.left.max_end > query.start:
            self._search_overlap(node.left, query, found)
        if node.interval.overlaps(query):
            found.append(node.interval)
        # Prune the right subtree: everything in it starts at or after
        # this node's start, so if that start is >= query.end, no right
        # interval can overlap.
        if node.right is not None and node.interval.start < query.end:
            self._search_overlap(node.right, query, found)

    def find_containing(self, point: float) -> list[Interval]:
        """All stored intervals containing ``point``, in start order."""
        found: list[Interval] = []
        self._search_point(self._root, point, found)
        return found

    def _search_point(
        self, node: Optional[_Node], point: float, found: list[Interval]
    ) -> None:
        if node is None:
            return
        if node.left is not None and node.left.max_end > point:
            self._search_point(node.left, point, found)
        if node.interval.contains_point(point):
            found.append(node.interval)
        if node.right is not None and node.interval.start <= point:
            self._search_point(node.right, point, found)

    def has_conflict(self, query: Interval) -> bool:
        """True when any stored interval overlaps ``query`` (early exit)."""
        return self._search_any(self._root, query)

    def _search_any(self, node: Optional[_Node], query: Interval) -> bool:
        if node is None:
            return False
        if node.left is not None and node.left.max_end > query.start:
            if self._search_any(node.left, query):
                return True
        if node.interval.overlaps(query):
            return True
        return bool(
            node.right is not None
            and node.interval.start < query.end
            and self._search_any(node.right, query)
        )

    # -- container protocol ----------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __contains__(self, interval: object) -> bool:
        if not isinstance(interval, Interval):
            return False
        return self._contains(self._root, interval)

    def _contains(self, node: Optional[_Node], interval: Interval) -> bool:
        if node is None:
            return False
        if interval < node.interval:
            return self._contains(node.left, interval)
        if interval > node.interval:
            return self._contains(node.right, interval)
        return True

    def __iter__(self) -> Iterator[Interval]:
        """Intervals in ascending start order (in-order traversal)."""
        stack: list[_Node] = []
        node = self._root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.interval
            node = node.right
