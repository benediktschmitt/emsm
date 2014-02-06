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


# Modules
# ------------------------------------------------
import argparse


# Classes
# ------------------------------------------------
class ArgumentParser(object):
    """
    Wraps the argparse.ArgumentParser object, that is used by the application.
    """

    def __init__(self, app):
        self._app = app

        self.argparser = argparse.ArgumentParser(
            description="Extendable Minecraft Server Manager (EMSM)",
            epilog=("Visit https://github.com/benediktschmitt/emsm for "
                    "further information."),
            add_help=True
            )

        # This subparser group contains the subparsers of all plugins.
        self.plugin_parsers = self.argparser.add_subparsers(
            title="plugin", dest="plugin",
            description="The name of the plugin, you want to invoke."
            )

        # Contains all parsed arguents
        self.args = None
        return None

    def parse_args(self):
        """
        Parses all arguments and stores them in *self.args*.
        """
        self.args = self.argparser.parse_args()
        return None

    def add_app_args(self):
        """
        Adds the global arguments to the argparser. These are:
        """
        self.argparser.add_argument(
            "--version", action="version",
            version="EMSM {}".format(self._app.version)
            )

        worlds_group = self.argparser.add_mutually_exclusive_group()
        worlds_group.add_argument(
            "-w", "--world",
            action = "append",
            dest = "worlds",
            metavar = "WORLD",
            choices = self._app.conf.worlds.sections(),
            default = list(),
            help = "Selects single worlds."
            )
        worlds_group.add_argument(
            "-W", "--all-worlds",
            action = "store_const",
            dest = "all_worlds",
            const = True,
            default = False,
            help = "Selects all available worlds."
            )

        server_group = self.argparser.add_mutually_exclusive_group()
        server_group.add_argument(
            "-s", "--server",
            action = "append",
            dest = "server",
            metavar = "SERVER",
            choices = self._app.conf.server.sections(),
            default = list(),
            help = "Selects single server software."
            )
        server_group.add_argument(
            "-S", "--all-server",
            action = "store_const",
            dest = "all_server",
            const = True,
            default = False,
            help = "Selects all available server software."
            )
        return None
