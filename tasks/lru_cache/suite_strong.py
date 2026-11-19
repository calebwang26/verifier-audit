"""Strong suite: edge cases & random checks against the oracle."""
import random

import solution
from solution import LRUCache
from spec import apply, gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_get_counts_as_use():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == 10      # key 1 is now the most recently used
    cache.put(3, 30)               # so key 2 is the one thrown out
    assert cache.get(2) == -1
    assert cache.get(1) == 10
    assert cache.get(3) == 30


def test_overwrite_counts_as_use():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(1, 11)               # key 1 is now the most recently used
    cache.put(3, 30)
    assert cache.get(2) == -1
    assert cache.get(1) == 11


def test_overwrite_does_not_evict():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(2, 21)
    assert cache.get(1) == 10
    assert cache.get(2) == 21


def test_capacity_one():
    cache = LRUCache(1)
    cache.put(1, 10)
    assert cache.get(1) == 10
    cache.put(2, 20)
    assert cache.get(1) == -1
    assert cache.get(2) == 20


def test_cache_fills_exactly_to_capacity():
    cache = LRUCache(3)
    for key in (1, 2, 3):
        cache.put(key, key * 10)
    assert [cache.get(key) for key in (1, 2, 3)] == [10, 20, 30]


def test_stored_zero_is_not_confused_with_missing():
    cache = LRUCache(2)
    cache.put(5, 0)
    assert cache.get(5) == 0
    assert cache.get(6) == -1


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        capacity, ops = gen_input(rng)
        assert apply(solution, (capacity, ops)) == oracle(capacity, ops)
