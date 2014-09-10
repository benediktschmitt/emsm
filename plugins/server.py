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

This plugin provides a user interface for the server wrapper. It can handle
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Arguments
---------
 
Select the server with the *common* arguments **--server** or **--all-server**.

.. option:: --usage

    Prints the names of the worlds, powered by this server.
"""


# Modules
# ------------------------------------------------

# std
import os

# local
import emsm
from emsm.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "Server"

    
# Classes
# ------------------------------------------------
    
class Server(BasePlugin):
    
    VERSION = "3.0.0-beta"

    DESCRIPTION = __doc__
    
    def __init__(self, application, name):
        """
        """
        BasePlugin.__init__(self, application, name)
        
        self.setup_argparser()
        return None

    def setup_argparser(self):
        """
        Sets the argument parser of this plugin up.
        """
        parser = self.argparser()
        
        parser.description = "Manage your server executables"

        parser.add_argument(
            "--usage",
            action = "count",
            dest = "usage",
            help = "Prints all worlds powered by a server."
            )

        parser.add_argument(
            "--list",
            action = "count",
            dest = "list",
            help = "Prints the names of all server supported by the EMSM."
            )
        return None

    def run(self, args):
        """
        ...
        """
        for server in self.app().server().get_selected():            
            if args.usage:
                self._print_usage(server)
                
        if args.list:
            self._print_list()
        return None

    def _print_usage(self, server):
        """
        Prints all worlds that are powered by the *server*.
        """
        # Get all worlds powered by this server.
        worlds = self.app().worlds().get_by_pred(
            lambda w: w.server() is server
            )
        online_worlds = list(filter(lambda w: w.is_online(), worlds))
        offline_worlds = list(filter(lambda w: w.is_offline(), worlds))
        
        # Print the worlds grouped by their current status (offline/online).
        print("server - {} - usage:".format(server.name()))
        print("\t", "number of worlds:", len(worlds))

        if online_worlds:
            print("\t", "online:")
            for world in online_worlds:
                print("\t\t", world.name())

        if offline_worlds:
            print("\t", "offline:")
            for world in offline_worlds:
                print("\t\t", world.name())
        return None

    def _print_list(self):
        """
        Prints a list with the names of all available server.
        """
        names = self.app().server().get_names()
        names.sort()

        print("server - list:")
        for name in names:
            print("\t", name)
        return None
