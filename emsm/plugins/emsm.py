#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2014-2018 <see AUTHORS.txt>
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

Changelog
---------

*   EMSM 5.0.3b0

    Removed the **--check-update** action. Using *pip* to check for updates
    is more reliable and the preferred way:

    .. code-block:: bash

        $ pip3 list -o | grep emsm

    *   https://github.com/benediktschmitt/emsm/issues/67
    *   https://github.com/benediktschmitt/emsm/issues/69
"""


# Modules
# ------------------------------------------------

# std
import os
import logging

# local
import emsm
from emsm.core.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "EMSM"

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class EMSM(BasePlugin):

    VERSION = "5.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, app, name):
        super().__init__(app, name)

        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        """
        # When using the configuration for this plugin, make sure to not
        # interfere with the global emsm configuration section (this section
        # contains the *user* and *timeout* options).
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
            dest = "emsm_version",
            help = "Shows the current EMSM version number."
            )
        me_group.add_argument(
            "--license",
            action = "count",
            dest = "emsm_license",
            help = "Shows the EMSM license.",
            )
        return None

    def _action_version(self):
        """
        Displays the current emsm version number and hash value of the last git
        commit.
        """
        print(emsm.core.version.VERSION)
        return None

    def _action_license(self):
        """
        Prints the EMSM license.
        """
        print(emsm.core.license_.LICENSE)
        return None

    def run(self, args):
        """
        """
        if args.emsm_version:
            self._action_version()
        elif args.emsm_license:
            self._action_license()
        return None
