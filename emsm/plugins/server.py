#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2014-2016 Benedikt Schmitt <benedikt@benediktschmitt.de>
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

This plugin provides a user interface for the server wrapper. It can handle
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

.. code-block:: ini

    [server]
    update_message = The server is going down for an update.
        Come back soon.

**update_message**

    Message sent to a world before stopping the world due to an server
    update.

Arguments
---------

.. note::

    Make sure to select the server via ``-s, --server``.

.. option:: --usage

    Prints the names of the worlds, powered by a server.

.. option:: --list

    Prints the names of all server supported by the EMSM.

.. option:: --update

    Updates the server software.
"""


# Modules
# ------------------------------------------------

# std
import os
import sys
import logging

# third party
import termcolor

# local
import emsm
from emsm.core.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "Server"

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class Server(BasePlugin):

    VERSION = "5.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, application, name):
        """
        """
        BasePlugin.__init__(self, application, name)

        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        Reads all configuration options.
        """
        conf = self.global_conf()

        self._update_message = conf.get(
            "update_message",
            "The server is going down for an update.\nCome back soon."
            )
        conf["update_message"] = self._update_message
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser of this plugin up.
        """
        parser = self.argparser()

        parser.description = "Manage your server executables"

        # We allow only one argument (keep it simple).
        me_group = parser.add_mutually_exclusive_group()
        me_group.add_argument(
            "--usage",
            action = "count",
            dest = "server_usage",
            help = "Prints all worlds powered by a server."
            )
        me_group.add_argument(
            "--list",
            action = "count",
            dest = "server_list",
            help = "Prints the names of all server supported by the EMSM."
            )
        me_group.add_argument(
            "--update",
            action = "count",
            dest = "server_update",
            help = "Updates the server software."
            )
        return None

    def run(self, args):
        """
        """
        if args.server_list:
            self._print_list()

        else:
            # Sort the server by their names, before running.
            sel_server = self.app().server().get_selected()
            sel_server.sort(key = lambda s: s.name())

            for server in sel_server:
                if args.server_usage:
                    self._print_usage(server)
                elif args.server_update:
                    self._update_server(server)
        return None

    def _print_usage(self, server):
        """
        Prints all worlds that are powered by the server *server*.
        """
        # Get all worlds powered by this server and sort them.
        worlds = self.app().worlds().get_by_pred(
            lambda w: w.server() is server
            )
        online_worlds = list(filter(lambda w: w.is_online(), worlds))
        online_worlds.sort(key = lambda w: w.name())

        offline_worlds = list(filter(lambda w: w.is_offline(), worlds))
        offline_worlds.sort(key = lambda w: w.name())

        # Print the worlds grouped by their current status (offline/online).
        print(termcolor.colored("{}:".format(server.name()), "cyan"))
        print("\t", "* {} worlds".format(len(worlds)))

        print("\t", "* {} online worlds".format(len(online_worlds)))
        if online_worlds:
            for world in online_worlds:
                print("\t\t", "- {}".format(world.name()))

        print("\t", "* {} offline worlds".format(len(offline_worlds)))
        if offline_worlds:
            for world in offline_worlds:
                print("\t\t", "- {}".format(world.name()))
        return None

    def _print_list(self):
        """
        Prints a list with the names of all available server software.
        """
        names = self.app().server().get_names()
        names.sort()

        for name in names:
            print("* {}".format(name))
        return None

    def _update_server(self, server):
        """
        Updates the server *server*.

        All worlds which are currently online and powered by the *server* will
        be stopped and restarted after the update.
        """
        print(termcolor.colored("{}:".format(server.name()), "cyan"))

        # Get all worlds, that are currently running the server.
        worlds = self.app().worlds().get_by_pred(
            lambda w: w.server() is server and w.is_online()
            )
        worlds.sort(key = lambda w: w.name())

        # Stop those worlds.
        try:
            for world in worlds:
                print("\t", "stopping the world '{}' ...".format(world.name()))
                world.stop(message=self._update_message)

        # Do not continue if a world could not be stopped.
        except emsm.core.worlds.WorldStopFailed as err:
            print("\t", termcolor.colored("error:", "red"),
                  "the world '{}' could not be stopped.".format(err.world.name())
                  )
            log.exception(err)

        # Continue with the server update if all worlds are offline.
        # Note, that a ServerIsOnlineError can not occur since we stopped
        # all worlds. (If a world would still be online, we would not have
        # reached this line of code.)
        else:
            print("\t", "reinstalling the server ...")
            try:
                server.reinstall()
            except emsm.core.server.ServerInstallationFailure as err:
                print("\t", termcolor.colored("error:", "red"), err)
                log.exception(err)

        # Restart the worlds.
        finally:
            for world in worlds:
                print("\t", "restarting the world '{}' ..."\
                      .format(world.name()))
                try:
                    world.start()
                except emsm.core.worlds.WorldStartFailed as err:
                    print("\t", termcolor.colored("error:", "red"),
                          "the world '{}' could not be restarted."\
                          .format(err.world.name())
                          )
                    log.exception(err)
        return None
