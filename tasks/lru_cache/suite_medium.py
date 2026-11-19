"""Medium suite: the tests a typical repo would have."""
from solution import LRUCache
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_missing_key_returns_minus_one():
    cache = LRUCache(2)
    assert cache.get(7) == -1


def test_oldest_key_is_evicted():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(3, 30)
    assert cache.get(1) == -1
    assert cache.get(2) == 20
    assert cache.get(3) == 30


def test_put_overwrites_value():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(1, 11)
    assert cache.get(1) == 11
