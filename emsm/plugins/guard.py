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

Monitors selected worlds (*--world*, *-w*, *-W*) and reacts on issues.

Download
--------

You can find the latest version of this plugin in the EMSM
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

Since EMSM version 3.2.2-beta, this plugin requires no more configuration.
The command line arguments allow you to adjust the guard for each world.

Arguments
---------

When invoked all worlds selected with the global EMSM commands *-W* or *-w*
are checked.

.. option:: --error-action {none, stop, restart}

    Defines how the guard handles a world in trouble.

.. note::

    Per default, all tests will be performed. If you don't want to run all
    tests, you can pass the tests, which should be performed as command
    line arguments.

.. option:: --test-status

    Check if the world is online.

.. option:: --test-log

    Check if the logs contain an error.

.. option:: --test-port

    Check if the world is reachable.

.. option:: --output-format {console, text}

    Defines the output format.

    *text* is suitable for sending the guard output via email.

.. option:: --output-only-new-warnings

    If an error with the world has been detected in the previous run, the
    warning for this world will be suppressed.

Cron
----

This plugin is made for cron (therefore it does not print much):

.. code-block:: text

    # m h dom mon dow user command
    # Runs the guard every 5 minutes for all worlds
    */5 * *   *   *   root minecraft -W guard --output-only-new-warnings --output-format text

    # Runs the guard every 5 minutes for the world *foo*.
    */5 * *   *   *   root minecraft -w foo guard --output-only-new-warnings --output-format text

Changelog
---------

3.0.0-beta

    * Removed configuration options that were dedicated to enable the guard
      for selected worlds.
    * The *new* guard simply monitors all worlds selected with the **-W**
      or **-w** argument.

3.2.2-beta

    * removed configuration options
    * added   port check again
    * added   different output formats
"""


# Modules
# ------------------------------------------------

# std
import os
import re
import sys
import time
import socket
import logging
import json

# third party
import termcolor

# local
import emsm
from emsm.core.base_plugin import BasePlugin


# Backward compatibility
# ------------------------------------------------

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError


# Data
# ------------------------------------------------

PLUGIN = "Guard"

log = logging.getLogger(__file__)


# Exceptions
# ------------------------------------------------

class TestFailure(Exception):
    """
    Raised by a guard world test method, if a world did not pass the test.
    """

    def __init__(self, world, test_name, message=None):
        self.world = world
        self.test_name = test_name
        self.message = message
        return None

    def __str__(self):
        if not self.message is None:
            tmp = "The world '{}' did not pass the guard test '{}': {}"\
                  .format(self.world.name(), self.test_name, self.message)
        else:
            tmp = "The world '{}' did not pass the guard test '{}."\
                  .format(self.world.name(), self.test_name)
        return tmp


# Functions
# ------------------------------------------------

def port_is_open(adr, timeout=1, attempts=1):
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

    VERSION = "5.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, app, name):
        """
        """
        BasePlugin.__init__(self, app, name)
        self._setup_argparser()

        # We save information about the world health status and occured errors
        # in the guard database. Read more below.
        self._guard_db = None
        self._load_guard_db()
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()
        parser.description = "Monitors the worlds and reacts on issues."

        # Test selection
        tests_group = parser.add_argument_group(
            title = "tests",
            description = ("You can define which tests are performed, by "
                           "passing one of these arguments. If no test is "
                           "selected, all tests are performed."
                           )
            )
        tests_group.add_argument(
            "--test-status",
            action = "count",
            dest = "guard_test_status",
            help = "Check if the world is online."
            )
        tests_group.add_argument(
            "--test-log",
            action = "count",
            dest = "guard_test_log",
            help = "Check if the logs contain an error."
            )
        tests_group.add_argument(
            "--test-port",
            action = "count",
            dest = "guard_test_port",
            help = "Check if the world's server is reachable."
            )

        # Error action
        parser.add_argument(
            "--error-action",
            action = "store",
            choices = ("none", "stop", "restart"),
            default = "none",
            dest = "guard_error_action",
            help = "Defines the reaction on detected errors."
            )

        # Output
        output_group = parser.add_argument_group(
            title = "output",
            description = ("You can change the output format or restrict the "
                           "amount of printed warnings.")
            )
        output_group.add_argument(
            "--output-format",
            action = "store",
            choices = ("console", "text"),
            default = "console",
            dest = "guard_output_format",
            help = "Defines the output format."
            )
        output_group.add_argument(
            "--output-only-new-warnings",
            action = "count",
            dest = "guard_output_only_new_warnings",
            help = "Prints only new warnings."
            )
        return None

    # Guard database

    """
    We store some data about the worlds health, so that we are able to print a
    warning for the same error only once.

    The guard db is simply a json serialized dictionary, which stores only
    information about worlds which are *already* in trouble:

        {'myworld': {'failed_test': 'status',
                     'test_message': 'world is offline',
                     'time': 1418996881.327088,
                     'warning_printed': False
                     }
         'world2': ...
        }

    A world is removed from this database, as soon as it is restarted or if
    it passes all tests.
    """

    def _guard_db_path(self):
        """
        """
        return os.path.join(self.data_dir(), "errors.json")

    def _load_guard_db(self):
        """
        """
        try:
            with open(self._guard_db_path()) as file:
                self._guard_db = json.load(file)
        except (IOError, FileNotFoundError):
            self._guard_db = dict()
        return None

    def _save_guard_db(self):
        """
        """
        with open(self._guard_db_path(), "w") as file:
            json.dump(self._guard_db, file)
        return None

    # World health checks

    """
    When a test method detects a problem with the world, it raises a
    ``TestFailedError`` exception.
    """

    def _test_status(self, world):
        """
        This test fails, if the world is offline or has been launched multiple
        times.
        """
        pids = world.pids()

        # Check if the world is offline.
        if len(pids) == 0:
            raise TestFailure(world, "status", "world is offline")

        # Check if the world has been launched multiple times.
        if len(pids) >= 2:
            raise TestFailure(
                world, "status", "world has been launched more than one time."
                )
        return None

    def _test_log(self, world):
        """
        This test failes, if the log contains a severe error.
        """
        # Search the log for error records.
        error_re = world.server().log_error_re()
        log = world.latest_log()

        res = re.search(error_re, log)
        if res:
            raise TestFailure(world, "log", str(res))
        return None

    def _test_port(self, world):
        """
        This test fails, if the world's port is not open.
        """
        ip, port = world.address()

        # Check if the EMSM could retrieve the world's address.
        if port is None:
            log.warning("port test for '{}' could not be performed, since the "
                        "world's address could not be retrieved."
                        )
        # Check if we can create a connection to the address and raise an
        # error if not.
        elif not port_is_open((ip, port), timeout=1, attempts=5):
            raise TestFailure(world, "port")
        return None

    def _test(self, world, args):
        """
        Performs the via *args* selected tests on the world, to check if
        everything works fine.
        """
        # Todo: If the number of tests gets bigger, it would be wise
        #       to replace this with loops.

        do_all_tests = not (args.guard_test_status \
                            or args.guard_test_log \
                            or args.guard_test_port
                            )

        if do_all_tests or args.guard_test_status:
            self._test_status(world)
        if do_all_tests or args.guard_test_log:
            self._test_log(world)
        if do_all_tests or args.guard_test_port:
            self._test_port(world)
        return None

    # Error reaction

    def _handle_error(self, world, args):
        """
        The *world* is in trouble. This method reacts on the world's issues
        with the defined *errro_action* in *args*.
        """
        # I assume, that no error happens here.
        if args.guard_error_action == "none":
            pass
        elif args.guard_error_action == "stop":
            world.stop(force_stop=True)
        elif args.guard_error_action == "restart":
            world.restart(force_restart=True)
        return None

    def _guard(self, world, args):
        """
        Tests if the world is in trouble. Reacts if necessairy on issues and
        saves information about the world's status in the guard database.
        """
        try:
            self._test(world, args)
        except TestFailure as err:
            log.warning(err)

            # Note, that *db_record* is actually a reference and not only
            # a copy.
            db_record = self._guard_db.get(world.name(), dict())
            self._guard_db[world.name()] = db_record

            # Handle the error, if we did not react earlier on it
            # or if the error_action changed.
            if db_record.get("error_action") is None \
               or db_record.get("error_action") != args.guard_error_action:
                self._handle_error(world, args)

            # Update the guard database.
            db_record["failed_test"] = err.test_name
            db_record["test_message"] = err.message
            db_record["test_time"] = time.time()
            db_record["error_action"] = args.guard_error_action
            db_record["warning_printed"] = db_record.get("warning_printed", False)
        else:
            # The world is running fine. So we can remove it from the
            # error database, if it was registered.
            if world.name() in self._guard_db:
                self._guard_db.pop(world.name())
        return None

    # Output

    def _print_status_text(self, world, db_record):
        """
        """
        print(world.name())
        print("="*len(world.name()))
        print()
        print("failed_test:  ", db_record["failed_test"])
        print("test_message: ", db_record["test_message"])
        print("test_time:    ", time.ctime(db_record["test_time"]))
        print("error_action: ", db_record["error_action"])
        print()
        print()
        return None

    def _print_status_console(self, world, db_record):
        """
        """
        print(termcolor.colored("{}:".format(world.name()), "cyan"))
        print("\t", "failed_test:  ", db_record["failed_test"])
        print("\t", "test_message: ", db_record["test_message"])
        print("\t", "test_time:    ", time.ctime(db_record["test_time"]))
        print("\t", "error_action: ", db_record["error_action"])
        return None

    def _print_status(self, world, args):
        """
        Prints a warning if the world is in trouble or nothing, if not.
        """
        # Get the status report without altering the database.
        db_record = self._guard_db.get(world.name())

        # Break, if the world is not in trouble.
        # (This means that no records exists.)
        if db_record is None:
            return None

        # Break, if we should not print the same warning twice.
        if db_record.get("warning_printed", False) \
           and args.guard_output_only_new_warnings:
            return None

        # Print the status.
        if args.guard_output_format == "console":
            self._print_status_console(world, db_record)
        elif args.guard_output_format == "text":
            self._print_status_text(world, db_record)

        # Mark the status as already printed.
        db_record["warning_printed"] = True
        return None

    # --

    def run(self, args):
        """
        """
        # Run the guard for all selected worlds in alphabetical order.
        worlds = self.app().worlds().get_selected()
        worlds.sort(key = lambda w: w.name())
        for world in worlds:
            self._guard(world, args)
            self._print_status(world, args)

        # Save any changes made during the run.
        self._save_guard_db()
        return None
