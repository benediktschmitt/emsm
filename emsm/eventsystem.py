#!/usr/bin/env python


# Data
# ------------------------------------------------
__all__ = ["Signal", "Dispatcher"]


# Classes
# ------------------------------------------------
class Signal(object):
    """
    A simple signal.

    """

    def __init__(self, name):
        self._slots = list()
        self._name = name
        return None

    name = property(lambda self: self._name)

    def connect(self, slot):
        if not slot in self._slots:
            self._slots.append(slot)
        return None

    def disonncet(self, slot):
        try:
            temp = self._slots.index(slot)
            self._slots.pop(slot)
        except IndexError:
            pass
        return None

    def emit(self, *args, **kargs):
        """
        Blocks, until all blocks were called. If an error occures,
        it will be ignored and reraised when all slots were called.
        """
        error = None

        for slot in self._slots:
            try:
                slot(*args, **kargs)
            except Exception as e:
                if error is None:
                    error = e

        if error:
            raise error
        return None


class Dispatcher(object):
    """
    A simple dispatcher

    For convenience, all signals can only be accessed by their
    names.
    """

    def __init__(self):
        self._signals = dict()
        return None

    def add_signal(self, name):
        """
        Adds the signal to the dispatcher if it
        does not exist and returns it.
        """
        if not name in self._signals:
            self._signals[name] = Signal(name)
        return self._signals[name]

    def has_signal(self, name):
        return name in self._signals

    def get_signal(self, name):
        return self._signals[name]

    def connect(self, slot, signal, create=False):
        """
        Connects the signal with the slot. If the signal does not
        exist and create is true, the signal will be created.
        """
        if create:
            self.add_signal(signal)
        self._signals[signal].connect(slot)
        return None

    def emit(self, signal, *args, **kwargs):
        """
        Emits the signal with the given args and kwargs.
        """
        self._signals[signal].emit(*args, **kwargs)
        return None