"""A least-recently-used cache with a fixed capacity.

get(key) returns the stored value, or -1 if the key isn't there.
put(key, value) stores a value. When the cache is over capacity, the key
that was used (read or written) longest ago is thrown out.
"""
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = OrderedDict()

    def get(self, key):
        if key not in self.items:
            return -1
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key, value):
        if key in self.items:
            self.items.move_to_end(key)
        self.items[key] = value
        if len(self.items) > self.capacity:
            self.items.popitem(last=False)
