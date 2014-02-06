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
=====
Works as interface between the linux initd service and the EMSM.


Installation
============
Copy the *initd_script* from the *emsm* directory to */etc/init.d/minecraft*
and run *update-rc.d minecraft*.


Configuration
=============

main.conf
---------
[initd]
manage_all_worlds = no

Where
^^^^^
    * manage_all_worlds
        If yes, all worlds are automatically started/stopped if the runlevel
        demands it.

worlds.conf
-----------
[foo]
enable_initd = no

Where
^^^^^
    * enable_initd
        Is the local value for *manage_all_worlds*.


Arguments
=========
* --start
    Starts all worlds, where the *enable_initd* configuration value is true.
* --stop
    Stops all worlds, where the *enable_initd* configuration value is true.


Events
======
* initd_start()
* initd_stop()
"""


# Modules
# ------------------------------------------------
# local
import world_wrapper
from base_plugin import BasePlugin
from app_lib import userinput


# Data
# ------------------------------------------------
PLUGIN = "InitD"

   
# Classes
# ------------------------------------------------   
class InitD(BasePlugin):
    """
    Connection to the diffrent runlevel of a linux system.
    Emits events corresponding to the *service minecraft [cmd]*
    command:

    * service minecraft start -> emit("initd_start")
    * service minecraft stop -> emit("initd_stop")

    This plugin comes with a bash script that must be copied to the
    */etc/init.d/* directory. (The bash script is in the *emsm* source folder.)
    After copying the script to the *init.d* directory, don't forget to run
    *update-rc minecraft*.
    """

    version = "2.0.0"
    
    def __init__(self, app, name):
        BasePlugin.__init__(self, app, name)

        self.initd_start = self.app.events.get_event("initd_start")
        self.initd_stop = self.app.events.get_event("initd_stop")

        self.start_occured = False
        self.stop_occured = False

        self.setup_conf()
        self.setup_argparser()
        return None

    def setup_conf(self):
        self.manage_all_worlds = self.conf.getboolean("manage_all_worlds", False)

        self.conf["manage_all_worlds"] = "yes" if self.manage_all_worlds else "no"
        return None
    
    def setup_argparser(self):
        self.argparser.description = (
            "Emits corresponding to the current runlevel diffrent event."
            "Make sure, that you copied the *emsm/initd_script* to "
            "*/etc/init.d/minecraft*.")

        # Only one runlevel to the same time.
        me_group = self.argparser.add_mutually_exclusive_group()
        me_group.add_argument(
            "--start",
            action="count", dest="initd_start",
            help="Emits the initd_start event.")
        me_group.add_argument(
            "--stop",
            action="count", dest="initd_stop",
            help="Emits the initd_stop event.")
        return None

    def uninstall(self):
        super().uninstall()

        if userinput.ask("Do you want to remove the changes in world.conf?"):
            world_conf = self.app.conf.worlds
            for section in world_conf:
                world_conf.remove_option(section, "enable_initd")
        return None

    # initd event handling
    # --------------------------------------------

    def _enabled_initd(self, world):
        """
        Returns true, if the world is managed with initd.
        """
        # Try to get the 'local' value
        try:
            tmp = world.conf.getboolean("enable_initd")
        except ValueError:
            pass
        else:
            if tmp is not None:
                return tmp
        # Fallback to the the 'global' value.
        return self.manage_all_worlds

    def auto_start(self):
        """
        Starts all worlds if initd is enabled.
        
        The output of this function is optimized for *./lib/lsb/init-functions*
        """
        worlds = self.app.worlds.get_by_pred(
            lambda w: w.is_offline() and self._enabled_initd(w))
        
        err = None
        for world in worlds:
            try:
                world.start()
            except world_wrapper.WorldStartFailed as tmp_err:
                msg = "Start of the world '{}' failed.".format(world.name)
                self.log.error(msg)
                if err is None:
                    err = tmp_err
            else:
                print(world.name, " ", sep="", end="")
        if err:
            exit(1)
        return None

    def auto_stop(self):
        """
        Stops all worlds if initd is enabled. Optimized for a fast
        shutdown of all worlds.
        
        The output of this function is optimized for *./lib/lsb/init-functions*
        """
        worlds = self.app.worlds.get_by_pred(
            lambda w: w.is_online() and self._enabled_initd(w))

        for world in worlds:
            world.send_command("save-all")
            world.send_command("stop")

        err = None
        for world in worlds:
            try:
                world.stop(force_stop=True)
            except world_wrapper.WorldIsOfflineError:
                pass
            except world_wrapper.WorldStopFailed as tmp_err:
                msg = "Stop of the world '{}' failed.".format(world.name)
                self.log.error(msg)
                if err is None:
                    err = tmp_err

            if world.is_offline():
                print(world.name, " ", sep="", end="")
        if err:
            exit(1)
        return None
    
    # Run
    # --------------------------------------------
    
    def run(self, args):
        if args.initd_start:
            self.start_occured = True
            self.auto_start()
            self.log.debug("Emitting *initd_start* event.")
            self.initd_start.emit()
        elif args.initd_stop:
            self.stop_occured = True
            self.auto_stop()
            self.log.debug("Emitting *initd_stop* event.")
            self.initd_stop.emit()
            # Exit directly to avoid the *finish* runlevel of the EMSM.
            exit(0)
        return None
