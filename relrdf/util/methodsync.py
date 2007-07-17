import threading


class SyncMethodsMixin(object):
    """A mixing class that makes it possible to declare methods as
    synchonized.

    Synchronized methods are mutualy exclusive for a particular
    instance, that is, if one synchronized method is currently
    executing, attempts to start a second synchronized method from
    other threads will block until the method finishes. The
    `synchronized` decorator in this module marks methods as
    synchronized."""
    
    __slots__ = ('_methodLock')

    def __init__(self, *args, **keywords):
        super(SyncMethodsMixin, self).__init__(*args, **keywords)

        self._methodLock = threading.Lock()


def synchronized(method):
    """A decorator that makes a method synchronized.

    In order for this decorator to work, the class containing the
    method must inherit from the `SyncMethodsMixin` class in this
    module."""

    def wrapper(self, *args, **keywords):
        self._methodLock.acquire()
        try:
            return method(self, *args, **keywords)
        finally:
            self._methodLock.release()

    return wrapper
