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

"""
About
-----

Works as interface between the linux *initd service* and the EMSM.

Download
--------

You can find the latest version of this plugin in the EMSM  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Installation
------------

The EMSM comes with an ``init.d`` script. You need to copy it
to the ``/etc/init.d`` directory so that EMSM works with the
*init.d* service.

.. code-block:: bash

    $ foo@bar: cp emsm/initd_script /etc/init.d/minecraft
    $ foo@bar: chmod +x /etc/init.d/minecraft
    $ foo@bar: update-rc.d minecraft
   

Configuration
-------------

worlds.conf
^^^^^^^^^^^

.. code-block:: ini

    [DEFAULT]
    enable_initd = yes

    [foo]
    enable_initd = no

**enable_initd**
   
    If ``True``, the autostart/-stop is enabled.

If you want to enable *init.d* for all worlds, use the *DEFAULT* section.
   
Arguments
---------

.. option:: --start

    Starts all worlds, where the *enable_initd* configuration value is true.

.. option:: --stop
   
    Stops all worlds, where the *enable_initd* configuration value is true.
"""


# Modules
# ------------------------------------------------

# std
import logging

# third party
import blinker

# local
import emsm
from emsm.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "InitD"

log = logging.getLogger(__file__)

   
# Classes
# ------------------------------------------------

class TerminalColor(object):
    """
    A small collection of methods to colorize terminal output.
    """

    RESET = "\x1b[39;49m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"

    @classmethod
    def to_red(cls, txt):
        return cls.RED + txt + cls.RESET

    @classmethod
    def to_green(cls, txt):
        return cls.GREEN + txt + cls.RESET


class InitD(BasePlugin):

    VERSION = "3.0.0-beta"

    DESCRIPTION = __doc__

    # Emitted when initd is called with the *--start* argument.
    on_initd_start = blinker.signal("initd_start")

    # Emitted when initd is called with the *--stop* argument.
    on_initd_stop = blinker.signal("initd_stop")
    
    def __init__(self, app, name):
        """
        """
        BasePlugin.__init__(self, app, name)

        self._setup_argparser()
        return None
    
    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()
        
        parser.description = "InitD interface"

        # Allow only one runlevel to the same time.
        me_group = parser.add_mutually_exclusive_group()
        me_group.add_argument(
            "--start",
            action = "count",
            dest = "initd_start",
            help = "Starts all worlds for which initd support is enabled."
            )
        me_group.add_argument(
            "--stop",
            action = "count",
            dest = "initd_stop",
            help = "Stop all worlds for which initd support is enabled."
            )
        me_group.add_argument(
            "--status",
            action = "count",
            dest = "initd_status",
            help = "Prints the status of all initd managed worlds."
            )
        return None

    def _uninstall(self):
        """
        Makes sure the configuration options added to the *world.conf* are
        removed.
        """
        # Clean the worlds.conf up.
        world_conf = self.app().conf().worlds()
        for section in world_conf:
            world_conf.remove_option(section, "enable_initd")
        return None

    def _initd_worlds(self):
        """
        Returns all worlds where *enable_initd* is true.

        See also:
            * WorldWrapper.conf()
        """
        worlds = self.app().worlds().get_by_pred(
            lambda w: w.conf().getboolean("enable_initd", False)
            )
        return worlds
    
    def _start(self):
        """
        Starts all worlds if *enable_initd* is true.
        """
        log.info("initd start ...")
        
        print("initd - start:")
        for world in self._initd_worlds():
            try:
                world.start()
            except emsm.worlds.WorldStartFailed as err:
                print("\t", TerminalColor.to_red("FAIL"), world.name())
                self.app().set_exit_code(2)
            else:
                print("\t", TerminalColor.to_green("OK  "), world.name())

        log.info("initd start done.")
        return None

    def _stop(self):
        """
        Stops all worlds if *enable_initd* is true.
        """
        log.info("initd stop ...")
        
        print("initd - stop:")
        for world in self._initd_worlds():
            try:
                # Because the process is killed anyway, we force it here.
                world.stop(force_stop=True)
            except emsm.worlds.WorldStopFailed as err:
                print("\t", TerminalColor.to_red("FAIL"), world.name())
                self.app().set_exit_code(2)
            else:
                print("\t", TerminalColor.to_green("OK  "), world.name())

        log.info("initd stop done.")
        return None

    def _status(self):
        """
        Prints the status of all worlds where *enable_initd* is true.
        """
        print("initd - status:")
        for world in self._initd_worlds():
            if world.is_online():
                print("\t", TerminalColor.to_green("ONLINE "), world.name())
            else:
                print("\t", TerminalColor.to_red("OFFLINE"), world.name())
        return None
    
    def run(self, args):
        """
        """
        if args.initd_start:
            self._start()
            InitD.on_initd_start.send()
        elif args.initd_stop:
            self._stop()
            InitD.on_initd_stop.send()
        elif args.initd_status:
            self._status()
        return None
