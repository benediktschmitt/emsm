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

Monitors selected worlds (*--world*, *-w*, *-W*) and reacts on issues.

Download
--------

You can find the latest version of this plugin in the EMSM  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

main.conf
^^^^^^^^^

.. code-block:: ini

    [guard]
    error_action = none
    error_regex = (\[SEVERE\])
   
**error_action**

    Defines the reaction on a detected error.

    * *none*     Do nothing
    * *restart*  Try to restart the world
    * *stop*     Try to stop the world.
    * *stderr*   Print a message to stderr
    
**error_regex**

    If this regex matches the log file, the world is considered to be in
    trouble.

Arguments
---------

The guard has no arguments. When invoked all worlds selected with the global
EMSM commands *-W* or *-w* are checked.

Please not, that the **guard** does not produce much output to ``stdout``, but
it writes a lot to the log files.
   
Cron
----

This plugin is made for cron (therefore it does not print much):

.. code-block:: text

    # m h dom mon dow user command
    # Runs the guard every 5 minutes for all worlds
    */5 * *   *   *   root minecraft -W guard
   
    # Runs the guard every 5 minutes for the world *foo*.
    */5 * *   *   *   root minecraft -w foo guard

Changelog
---------

.. versionchanged:: 3.0.0-beta

    * Removed configuration options that were dedicated to enable the guard
      for selected worlds.
    * The new **guard** simply monitors all worlds selected with the **-W**
      or *-w* argument.

Todo
----

* Add *email* as error action option.
"""


# Modules
# ------------------------------------------------

# std 
import re
import sys
import time
import socket
import logging

# local
import emsm
from emsm.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "Guard"

log = logging.getLogger(__file__)


# Functions
# ------------------------------------------------

def check_port(adr, timeout=1, attempts=1):
    """
    Returns `true` if the tcp address *ip*:*port* is reachable.

    Parameters:
        * adr
            The network address tuple of the target.
        * timeout
            Time in seconds waited until a connection attempt is
            considered to be failed.
        * attempts
            Number of port checks done until the *adr* is considered
            to be unreachable.
    """
    for i in range(attempts):
        s = socket.socket()
        s.settimeout(timeout)
        try:
            s.connect(adr)
        except Exception as err:
            pass
        else:
            return True
        finally:
            s.close()
    return False


# Classes
# ------------------------------------------------

class Guard(BasePlugin):
    
    VERSION = "3.0.0-beta"

    DESCRIPTION = __doc__
        
    def __init__(self, app, name):
        """
        """
        BasePlugin.__init__(self, app, name)

        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        Loads the configuration.
        """
        conf = self.conf()

        # Get the configuration options.
        self._error_action = conf.get("error_action")
        if self._error_action not in ("none", "restart", "stop", "stderr"):
            self._error_action = "stderr"

        self._error_regex = conf.get("error_regex", ".*\[SEVERE\].*")

        # Save the used configuration options and intialise the configuration.
        conf["error_action"] = self._error_action
        conf["error_regex"] = self._error_regex
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()

        parser.description = "Monitors the worlds and reacts on issues."
        return None

    def _world_in_trouble(self, world):
        """
        Returns ``True`` if the world is not running smooth.
        """
        # 1. Check if the world is online.
        error = world.is_offline()

        # 2. Check if the world's network address is reachable.
##        if not error:
##            error = not bool(check_port(world.address(), timeout=1, attempts=5))

        # 3. Check the log file for errors.
        if not error:
            log = world.latest_log()
            error = bool(re.search(self._error_regex, log))
        return error
            
    def guard(self, world):
        """
        Checks if the world is running *smooth* and reacts on issues.
        """
        # Break if we have nothing to do.
        if not self._world_in_trouble(world):
            return None
    
        log.warning("the world '{}' is not running correct."\
                    .format(world.name())
                    )

        # Restart
        if self._error_action == "restart":
            log.info("trying to restart the world '{}' ..."\
                     .format(world.name())
                     )
            try:
                world.restart(force_restart=True)
            except emsm.worlds.WorldStopFailed as err:
                log.warning("restart of '{}' failed: '{}'"\
                            .format(world.name(), err)
                            )
            except emsm.worlds.WorldStartFailed as err:
                log.warning("restart of '{}' failed: '{}'"\
                            .format(world.name(), err)
                            )
            else:
                log.info("restarted the world '{}'.".format(world.name()))

        # Stop
        elif self._error_action == "stop":
            log.info("trying to stop the world '{}' ..."\
                     .format(world.name())
                     )
            try:
                world.stop(force_stop=True)
            except emsm.worlds.WorldStopFailed as err:
                log.warning("could not stop the world '{}'."\
                            .format(world.name())
                            )
            else:
                log.info("stopped the world '{}'.".format(world.name()))

        # Stderr
        elif self._error_action == "stderr":
            print("guard - {}:".format(world.name()), file=sys.stderr)
            print("\t", "has issues", file=sys.stderr)
        return None

    def run(self, args):
        """
        """
        # Run the guard for all selected worlds.
        worlds = self.app().worlds().get_selected()
        for world in worlds:
            self.guard(world)
        return None
