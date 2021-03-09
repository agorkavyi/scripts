# Least Frequently Used Cache
# AG @ 2021

from collections import defaultdict
from collections import OrderedDict

# Helper class to store value and frequency count
class Node:
    def __init__(self, val: int, count: int):
        self.val = val
        self.count = count

# Main class of LFU cache with fixed capacity
class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.keyToNode = {}                         # map: key -> value and count
        self.countToNode = defaultdict(OrderedDict) # map: frequency count -> ordered dictionary of nodes with this frequency
        self.lfuCount = None                        # frequency of least used nodes in cache

    def get(self, key: int) -> int:
        if key not in self.keyToNode:
            return -1
        
        node = self.keyToNode[key]
        del self.countToNode[node.count][key]
        
        # Free up memory if this frequency map is empty now
        if not self.countToNode[node.count]:
            del self.countToNode[node.count]
        
        node.count += 1 # increment frequency count on every get()
        self.countToNode[node.count][key] = node
        
        # If least used frequency is empty adjust it
        if not self.countToNode[self.lfuCount]:
            self.lfuCount += 1
            
        return node.val

    def put(self, key: int, value: int) -> None:
        if not self.capacity:
            return
        
        if key in self.keyToNode:
            self.keyToNode[key].val = value
            self.get(key) # re-use getter code and adjust frequency of this key
            return
        
        if len(self.keyToNode) >= self.capacity:
            k,v = self.countToNode[self.lfuCount].popitem(last=False) # last=False will use FIFO order, so it will pop LRU key
            del self.keyToNode[k]
        
        self.countToNode[1][key] = self.keyToNode[key] = Node(value, 1)
        self.lfuCount = 1 # the lowest frequency now is 1 since we have a new item
        return

cache = LFUCache(3)
cache.put(2, 20)
cache.put(3, 30)
cache.put(1, 10)
print(cache.get(2))
print(cache.get(2))
cache.put(4, 40)
print(cache.get(1))
print(cache.get(3))