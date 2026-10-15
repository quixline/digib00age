"""Implement this class to create
a workable bucket for Limiter to use
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from queue import Queue
from threading import RLock


class AbstractBucket(ABC):
    """Base bucket interface"""

    def __init__(self, maxsize: int = 0, **_kwargs):
        self._maxsize = maxsize

    def maxsize(self) -> int:
        """Return the maximum size of the bucket,
        ie the maximum number of item this bucket can hold
        """
        return self._maxsize

    @abstractmethod
    def size(self) -> int:
        """Return the current size of the bucket,
        ie the count of all items currently in the bucket
        """

    @abstractmethod
    def put(self, item: float) -> int:
        """Put an item (typically the current time) in the bucket
        Return 1 if successful, else 0
        """

    @abstractmethod
    def get(self, number: int) -> int:
        """Get items, remove them from the bucket in the FIFO order, and return the number of items
        that have been removed
        """

    @abstractmethod
    def all_items(self) -> list[float]:
        """Return a list as copies of all items in the bucket"""

    @abstractmethod
    def flush(self) -> None:
        """Flush/reset bucket"""

    def inspect_expired_items(self, time: float) -> tuple[int, float]:
        """Find how many items in bucket that have slipped out of the time-window

        Returns:
            The number of unexpired items, and the time until the next item will expire
        """
        volume = self.size()
        item_count, remaining_time = 0, 0.0

        for log_idx, log_item in enumerate(self.all_items()):
            if log_item > time:
                item_count = volume - log_idx
                remaining_time = round(log_item - time, 3)
                break

        return item_count, remaining_time

    def lock_acquire(self):
        """Acquire a lock prior to beginning a new transaction, if needed"""

    def lock_release(self):
        """Release lock following a transaction, if needed"""


class MemoryQueueBucket(AbstractBucket):
    """A bucket that resides in memory using python's built-in Queue class"""

    def __init__(self, maxsize: int = 0, **_kwargs):
        super().__init__()
        self._q: Queue = Queue(maxsize=maxsize)

    def size(self) -> int:
        return self._q.qsize()

    def put(self, item: float):
        return self._q.put(item)

    def get(self, number: int) -> int:
        counter = 0
        for _ in range(number):
            self._q.get()
            counter += 1

        return counter

    def all_items(self) -> list[float]:
        return list(self._q.queue)

    def flush(self):
        while not self._q.empty():
            self._q.get()


class MemoryListBucket(AbstractBucket):
    """A bucket that resides in memory using python's List"""

    def __init__(self, maxsize: int = 0, **_kwargs):
        super().__init__(maxsize=maxsize)
        self._q: list[float] = []
        self._lock = RLock()

    def size(self) -> int:
        return len(self._q)

    def put(self, item: float):
        with self._lock:
            if self.size() < self.maxsize():
                self._q.append(item)
                return 1
            return 0

    def get(self, number: int) -> int:
        with self._lock:
            counter = 0
            for _ in range(number):
                self._q.pop(0)
                counter += 1

            return counter

    def all_items(self) -> list[float]:
        return self._q.copy()

    def flush(self):
        self._q = list()
