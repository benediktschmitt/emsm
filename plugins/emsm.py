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

Provides information about the EMSM itself, like the version and simplifies the
EMSM update.

Download
--------

You can find the latest version of this plugin in the EMSM
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Arguments
---------

.. option:: --version

    Shows the current EMSM version number.

.. option:: --license

    Shows the EMSM license.

.. option:: --check-update

    Simulates an EMSM update.

.. option:: --update

    Updates the EMSM.
"""


# Modules
# ------------------------------------------------

# std
import os
import re
import urllib.request

# local
import emsm
from emsm.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "EMSM"


# Classes
# ------------------------------------------------

class Updater(object):
    """
    Manages the EMSM update.
    """

    def __init__(self, app):
        self._app = app
        return None

    def latest_version(self):
        """
        Returns the latest EMSM version.
        """
        latest_version_py_url = "https://raw.githubusercontent.com/benediktschmitt/emsm/master/emsm/version.py"
        with urllib.request.urlopen(latest_version_py_url) as file:
            data = file.read()
            data = data.decode()

        # Isolte the *VERSION* variable value.
        latest_version = re.findall(
            "^VERSION\s*=\s*\\\"(.*?)\\\"\s*", data, re.MULTILINE
            )
        latest_version = latest_version[0]

        # Format the 
        latest_version = latest_version.split(".")
        return latest_version

    def update_needed(self):
        """
        Returns ``True`` if the current EMSM installation is out of date.
        """
        return None
        
    def update(self):
        """
        Updates the EMSM.
        """
        return None

    def simulate(self):
        """
        Simulates the EMSM update.
        """
        return None
    

class EMSM(BasePlugin):

    VERSION = "3.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, app, name):
        super().__init__(app, name)

        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        """
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()

        parser.description = "A manager for the EMSM itself"

        # We want to allow only one action per run, so we put everything in a
        # mutually exclusive group.
        me_group = parser.add_mutually_exclusive_group()
        me_group.add_argument(
            "--version",
            action = "count",
            dest = "version",
            help = "Shows the current EMSM version number."
            )
        me_group.add_argument(
            "--license",
            action = "count",
            dest = "license",
            help = "Shows the EMSM license.",
            )
        me_group.add_argument(
            "--check-update",
            action = "count",
            dest = "check_update",
            help = "Simulates an EMSM update."
            )
        me_group.add_argument(
            "--update",
            action = "count",
            dest = "update",
            help = "Updates the EMSM."
            )
        return None

    def _action_version(self):
        """
        Displays the current emsm version number and hash value of the last git
        commit.
        """
        print("version:", emsm.version.VERSION)
        print("commit hash:", None)
        return None

    def _action_license(self):
        """
        Prints the EMSM license.
        """
        print(emsm.license_.LICENSE)
        return None

    def _action_check_update(self):
        """
        Checks if the EMSM can be updated and simulates the update.
        """
        updater = Updater(self.app())
        updater.simulate()
        return None
        
    def _action_update(self):
        """
        Guides the user through an EMSM update.
        """
        updater = Updater(self.app())
        updater.update()
        return None
        
    def run(self, args):
        """
        """
        if args.version:
            self._action_version()
        elif args.license:
            self._action_license()
        elif args.check_update:
            self._action_check_update()
        elif args.update:
            self._action_update()
        return None
        

            
