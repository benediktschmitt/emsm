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

Controls each time the **EMSM** is invoked if the worlds are running and 
reachable from outside.

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
   auto_run = no
   guard_all_worlds = no
   
**error_action**

   Defines the reaction on a detected error.
   
   * *none*     Do nothing
   * *restart*  Try to restart the world
   * *stop*     Try to stop the world.
   * *stderr*   Print a message to stderr
    
**error_regex**

   If this regex matches the log file, it caues an error handling.
   
**auto_run**

   If yes, run each time, the EMSM is invoked.
   
**guard_all_worlds**

   If yes, this plugin guards all worlds per default.      
      
worlds.conf
^^^^^^^^^^^

.. code-block:: ini

   [foo]
   enable_guard = no
   
**enable_guard**
   
   Enables the guard for this plugin. Overwrites the global
   flag *guard_all_worlds*.

Summary
^^^^^^^
If you want to enable the plugin for almost all worlds, use the *enable_guard* 
option in the *DEFAULT* section:

.. code-block:: ini

   [DEFAULT]
   enable_guard = yes
   
   [foo]
   # This world is protected.
   
   [bar]
   # This world is not protected.
   enable_guard = no   

Arguments
---------

The guard has no arguments. If invoked it simply runs the guard for ALL worlds 
selected with the global *-W* or *-w* argument AND the worlds where 
*enable_guard* is true. 
   
Cron
----

This plugin is made for *cron*:

.. code-block:: text

   # m h dom mon dow user command
   # Runs the guard every 5 minutes for all worlds
   */5 * *   *   *   root minecraft -W guard
   
   # Runs the guard every 5 minutes for the world, where *enable_guard* is true:
   */5 * *   *   *   root minecraft guard   
"""


# Modules
# ------------------------------------------------
import re
import sys
import time
import socket

# local
import world_wrapper
from base_plugin import BasePlugin
from app_lib import userinput


# Data
# ------------------------------------------------
PLUGIN = "Guard"


# Functions
# ------------------------------------------------
def check_port(port, ip="", timeout=1):
    """
    Returns `true` if the tcp address *ip*:*port* is reachable.
    """
    adr = (ip, port)
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(adr)
    except socket.error:
        return False
    else:
        return True
    finally:
        s.close()


def world_is_listening(world, attempts=10, sleep_intervall=1):
    """
    Returns `true`, if the *world* is listening on it's address.
    """
    properties = world.get_properties()
    ip = properties.get("server-ip", "")
    port = properties.get("server-port", "")
    port = int(port) if port.isdigit() else 25565

    for i in range(attempts):
        if check_port(port, ip):
            return True
        time.sleep(sleep_intervall)
    return False

    
# Classes
# ------------------------------------------------   
class Guard(BasePlugin):
    """
    Provides automatic error handling for minecraft worlds.
    """

    # We want to finish at the end to make sure, that the status of a world is
    # not changed by another plugin.
    finish_priority = 1000
    
    version = "2.0.0"

    # It's useful to let other plugins prevent an automatical check.
    # E.g.: *initd*
    prevent_autorun = False
        
    def __init__(self, app, name):
        BasePlugin.__init__(self, app, name)

        # Configuration
        # Whats to do if a world is offline.
        self.error_action = self.conf.get("error_action")
        if self.error_action not in ("none", "restart", "stop", "stderr"):
            self.error_action = "none"

        self.error_regex = self.conf.get("error_regex", "(\[SEVERE\])")
        self.auto_run = self.conf.getboolean("auto_run", False)
        self.guard_all_worlds = self.conf.getboolean("guard_all_worlds", False)
               
        self.conf["error_action"] = self.error_action
        self.conf["error_regex"] = self.error_regex
        self.conf["auto_run"] = "yes" if self.auto_run else "no"
        self.conf["guard_all_worlds"] = "yes" if self.guard_all_worlds else "no"

        # Argparser
        self.argparser.description = (
            "Watches the logfiles and checks if the worlds are running smooth.")
        return None

    def uninstall(self):
        """
        Remove the additional configuration options in the worlds.conf.
        """
        super().uninstall()
        
        question = "Do you want to remove the additional "\
                   "options in worlds.conf?".format(self.name)
        if userinput.ask(question, default=True):
            worlds_conf = self.app.conf.worlds
            for section in worlds_conf:
                worlds_conf.remove_option(section, "enable_guard")
        return None

    # Run
    # --------------------------------------------

    def _enabled_guard(self, world):
        """
        Returns true, if the world should be guarded.
        """
        # Try to get the 'local' value
        try:
            tmp = world.conf.getboolean("enable_guard")
        except ValueError:
            pass
        else:
            if tmp is not None:
                return tmp
        # Fallback to the the 'global' value.
        return self.guard_all_worlds
    
    def guard(self, world):
        """
        Checks if the world is running.
        """
        # 1.) Check if the world is online
        # 2.) Make a port check
        # 3.) Check for errors in the log file.
        
        error = world.is_offline()
        # XXX Could be buggy if a world has been restarted a few seconds ago.
        error = error or not world_is_listening(world)
        if self.error_regex:
            error = error or re.search(self.error_regex, world.get_log())
        
        if error:
            msg = "The world '{}' is not running smooth.".format(world.name)
            self.log.warning(msg)
            
            if self.error_action == "restart":
                self.log.info("Trying to restart ...")
                try:
                    if world.is_online():
                        world.stop(force_stop=True)
                    world.start()
                except world_wrapper.WorldError:
                    self.log.warning("Restart failed.")
                else:
                    self.log.info("Restart complete.")
                
            elif self.error_action == "stop":
                self.log.info("Trying to stop the world ...")
                try:
                    if world.is_online():
                        world.stop(force_stop=True)
                except world_wrapper.WorldError:
                    self.log.warning("Stop failed.")
                else:
                    self.log.info("Stop complete.")
                
            elif self.error_action == "stderr":
                print("{}: '{}' seems to be offline"\
                      .format(self.name, world.name), file=sys.stderr)
        return None

    def run(self, args):
        # Check the selected worlds and the protected worlds.
        selected_worlds = self.app.worlds.get_selected()
        protected_worlds = self.app.worlds.get_by_pred(
            lambda w: self._enabled_guard(w))
        worlds = set()
        worlds.update(selected_worlds)
        worlds.update(protected_worlds)

        for world in worlds:
            self.guard(world)
        return None

    def finish(self):
        """
        This *run_check* should be the last action before exiting the programm.
        So I set the *finish_priority* extremly high.
        """
        if not (self.auto_run or self.prevent_autorun):
            return None
        
        worlds = self.app.worlds.get_by_pred(lambda w: self._enabled_guard(w))
        for world in worlds:
            self.guard(world)
        return None
