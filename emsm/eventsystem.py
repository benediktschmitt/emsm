#!/usr/bin/python3

# Extendable Minecraft Server Manager - EMSM
# Copyright (C) 2013-2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
