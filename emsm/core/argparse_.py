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
This module contains the :class:`ArgumentParser` class which wraps a
Python :class:`argparse.ArgumentParser` for the EMSM.
"""


# Modules
# ------------------------------------------------

# std
import argparse
import subprocess
import logging

# local
from .license_ import LICENSE
from .version import VERSION


# Data
# ------------------------------------------------

__all__ = [
    "LongHelpAction",
    "ArgumentParser"
    ]

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class LongHelpAction(argparse.Action):
    """
    Prints the *description* using less (if available) and exists.
    """

    def __init__(self, option_strings, description=None, dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS):
        """
        """
        self.description = description if description is not None else str()
        self.description.strip()

        super().__init__(
            option_strings = option_strings,
            dest = dest,
            default = default,
            nargs = 0,
            help = "shows the manual and exists"
            )
        return None

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Prints the :attr:`description`.
        """
        # We print the docstring under linux using *less*, if available.
        was_printed = False
        try:
            less_proc = subprocess.Popen("less", stdin=subprocess.PIPE)
            try:
                less_proc.stdin.write(self.description.encode())
                was_printed = True
            except IOError as err:
                print(err)
            finally:
                less_proc.stdin.close()
                less_proc.wait()
        except (OSError, ValueError) as err:
            pass

        # Use print() if nothing else worked.
        if not was_printed:
            print(self.description)
            was_printed = True

        parser.exit()
        return None


class ArgumentParser(object):
    """
    Wraps an :class:`argparse.ArgumentParser` instance.

    This class handles the *root* EMSM argument parser. The root parser
    only has a few global EMSM commands like ``-w``, ``-s``. Each plugin has
    its own subparser:

    .. code-block:: bash

        $ foo@bar: minecraft [emsm args] (plugin_name) [plugin args]

    **Example:**

    .. code-block:: bash

        # Call the *worlds* plugin with the world *foo* as target.
        $ foo@bar: minecraft -w foo worlds --status
    """

    def __init__(self, app):
        """
        """
        self._app = app

        self._argparser = argparse.ArgumentParser(
            description = "Extendable Minecraft Server Manager (EMSM)",
            epilog = "Visit https://github.com/benediktschmitt/emsm for "\
                     "further information.",
            add_help=True
            )

        # This subparser contains the parsers for the plugins.
        self._plugin_subparsers = self._argparser.add_subparsers(
            title = "plugin",
            dest = "plugin",
            description = "The name of the plugin, you want to invoke."
            )

        # Contains and caches the parsed arguments.
        self._args = None
        return None

    def argparser(self):
        """
        Returns the wrapped :class:`argparse.ArgumentParser` instance.
        """
        return self._argparser

    def args(self, cache=True):
        """
        Parses (if not yet done) the command line arguments and returns a
        namespace object that contains the result.

        :param bool cache:
            If ``True``, and the arguments have already been parsed, the
            result of the previous parse is returned.

        .. seealso::

            * :meth:`argparse.ArgumentParser.parse_args`
        """
        if self._args is None or not cache:
            log.info("parsing arguments ...".format(self._args))

            self._args = self._argparser.parse_args()

            log.info("parsed arguments: {}".format(self._args))
        return self._args

    def plugin_parser(self, plugin_name):
        """
        Returns the subparser for the plugin with the name *plugin_name*.
        """
        return self._plugin_subparsers.add_parser(plugin_name)

    def setup(self):
        """
        Adds the global EMSM arguments to the root argument parser.

        This method has to be called, when the
        :class:`~emsm.core.worlds.WorldManager` and
        :class:`~emsm.core.server.ServerManager` have been loaded, since we
        require the names of the available worlds and server.
        """
        log.info("adding emsm arguments ...")

        # The selectable worlds.
        worlds_group = self._argparser.add_mutually_exclusive_group()
        worlds_group.add_argument(
            "-w", "--world",
            action = "append",
            dest = "worlds",
            metavar = "WORLD",
            choices = self._app.worlds().get_names(),
            default = list(),
            help = "Selects the world."
            )
        worlds_group.add_argument(
            "-W", "--all-worlds",
            action = "store_const",
            dest = "all_worlds",
            const = True,
            default = False,
            help = "Selects all available worlds."
            )

        # The selectable server.
        server_group = self._argparser.add_mutually_exclusive_group()
        server_group.add_argument(
            "-s", "--server",
            action = "append",
            dest = "server",
            metavar = "SERVER",
            choices = self._app.server().get_names(),
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
