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

"""
About
=====
Watches the status of a world and restarts a world if necessairy.


Configuration
=============

main.conf
---------
[max_rows]
error_action = none
error_regex = (\[SEVERE\])
auto_run = no
guard_all_worlds = no

Where
^^^^^
* error_action
    Defines the reaction on a detected error.
    * none     Do nothing
    * restart  Try to restart the world
    * stop     Try to stop the world.
    * stderr   Print a message to stderr
* error_regex
    If this regex matches the log file, it caues an error handling.
* auto_run
    If yes, run each time, the EMSM is invoked.
* guard_all_worlds
    If yes, this plugin guards all worlds per default.

world.conf
----------
[foo]
enable_guard = no

Where
^^^^^
* enable_guard
    Enables the guard for this plugin. Overwrites the global
    flag *guard_all_worlds*.


Arguments
=========
Runs the guard for ALL worlds selected with the global *-W* or *-w* argument
AND the worlds where *enable_guard* is true.


Warnings
========
This plugin may behave not in the way you'd like to have it. Please make sure,
that the *error_regex* only matches what you want it to match.
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
            if args.guard:
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
