from time import time, sleep
from threading import Thread, RLock

class Cache():
    """
    A class to create cache entries
    """
    def __init__(self, key, value, ttl):
        self.key = key
        self.value = value
        self.ttl = time() + ttl
        self.expired = False
    
    """
    A function that checks if the object is expired or not
    """
    def isexpired(self):
        if self.expired is False:
            return self.ttl > time()
        else:
            return self.expired

class CacheList():
    """
    A class that keeps a list of cache entries
    """
    def __init__(self):
        self.list = []
        self.lock = RLock()

    """
    Add a entry to the list
    """
    def add_entry(self, cache):
        with self.lock:
            self.list.append(cache)

    """
    Get entry
    """
    def get_entry(self, key):
        with self.lock:
            for x in self.list:
                if x.key == key and x.isexpired():
                    return x.value
            return False