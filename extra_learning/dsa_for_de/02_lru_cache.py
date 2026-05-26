"""Simple LRU cache."""
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.store: OrderedDict = OrderedDict()

    def get(self, key):
        if key not in self.store:
            return None
        self.store.move_to_end(key)
        return self.store[key]

    def put(self, key, value) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1); cache.put("b", 2); cache.get("a"); cache.put("c", 3)
    print(list(cache.store.items()))
