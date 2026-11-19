"""Weak suite: one happy-path test."""
from solution import LRUCache


def test_put_then_get():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == 10
    assert cache.get(2) == 20
