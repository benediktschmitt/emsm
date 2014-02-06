#!/usr/bin/python3

# The MIT License (MIT)
# 
# Copyright (c) 2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


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
            self._slots.pop(temp)
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

    def __call__(self, *args, **kargs):
        """
        Convenient method for self.emit(...)
        """
        return self.emit(*args, **kargs)


class Dispatcher(object):
    """
    A simple dispatcher

    For convenience, all signals can only be accessed by their names.
    """

    def __init__(self):
        self._signals = dict()
        return None

    def get_event(self, name, create=True):
        """
        Returns the *Signal()* object, that corressponds to the *name*. If
        there's no *Signal()* with this *name*, a new Signal will be created.
        """
        if name not in self._signals:
            self._signals[name] = Signal(name)
        return self._signals[name]

    def connect(self, signal, slot, create=True):
        """
        Connects the signal with the slot. If the signal does not
        exist and create is true, the signal will be created.
        """
        if create:
            self.get_event(signal, create=True)
        self._signals[signal].connect(slot)
        return None

    def emit(self, signal, *args, **kwargs):
        """
        Emits the signal with the given args and kwargs.
        """
        self._signals[signal].emit(*args, **kwargs)
        return None
