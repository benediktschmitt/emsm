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


# Modules
# ------------------------------------------------

# std
import os
import pwd
import grp
import sys
import logging
import traceback

# third party
import filelock
import colorama
import termcolor

# local
from . import argparse_
from . import base_plugin
from . import conf
from . import logging_
from . import paths
from . import plugins
from . import server
from . import worlds
from . import license_
from . import version


# Data
# ------------------------------------------------

__all__ = [
    "ApplicationException",
    "WrongUserError",
    "Application"
    ]

log = logging.getLogger(__file__)


# Exceptions
# ------------------------------------------------

class ApplicationException(Exception):
    """
    Base class for all exceptions in this module.
    """


class WrongUserError(ApplicationException):
    """
    Raised if the EMSM is executed by the wrong user.
    """

    def __init__(self, required_user):
        self.required_user = required_user
        return None

    def __str__(self):
        temp = "This script requires a user named '{}'."\
               .format(self.required_user)
        return temp


# Classes
# ------------------------------------------------

class Application(object):
    """
    This class manages the initialisation and the complete run process
    of the EMSM.

    An EMSM application should be executed in a code structure similar to this
    one:

    .. code-block:: python

        app = Application()
        try:
            app.setup()
            app.run()
        except Exception as err:
            app.handle_exception()
            raise
        finally:
            exit(app.finish())
    """

    def __init__(self, instance_dir):
        """
        """
        # The order of the initialisation is not trivial!
        self._paths = paths.Pathsystem(instance_dir)
        self._lock = filelock.FileLock(
            os.path.join(self._paths.instance(), "app.lock")
            )
        self._logger = logging_.Logger(self)

        self._conf = conf.Configuration(self)
        self._argparser = argparse_.ArgumentParser(self)

        self._worlds = worlds.WorldManager(self)
        self._server = server.ServerManager(self)
        self._plugins = plugins.PluginManager(self)

        # The exit code can be changed by plugins. This is useful
        # since a plugin should not throw a SystemExit exception.
        self._exit_code = 0
        return None

    def paths(self):
        """
        Returns the used :class:`~emsm.core.paths.Pathsystem` instance.
        """
        return self._paths

    def conf(self):
        """
        Returns the used :class:`~emsm.core.conf.Configuration` instance.
        """
        return self._conf

    def argparser(self):
        """
        Returns the EMSM :class:`~emsm.core.argparse_.ArgumentParser`, that is
        used internally.
        """
        return self._argparser

    def worlds(self):
        """
        Returns the used :class:`~emsm.core.worlds.WorldManager` instance.
        """
        return self._worlds

    def server(self):
        """
        Returns the used :class:`~emsm.core.server.ServerManager` instance.
        """
        return self._server

    def plugins(self):
        """
        Returns the used :class:`~emsm.core.plugins.PluginManager` instance.
        """
        return self._plugins

    def exit_code(self):
        """
        Returns the exit code of the application.

        .. seealso:: :meth:`set_exit_code`
        """
        return self._exit_code

    def set_exit_code(self, code):
        """
        Sets the exit code to *code*. This is the exit code, that is used for
        the Python :func:`exit` function.

        :raises TypeError:
            if *code* is not an int.
        :raises ValueError:
            if *code* < 0.

        .. seealso::

            * :meth:`exit_code`
            * :func:`exit`
        """
        if not isinstance(code, int):
            raise TypeError("*code* is not an int.")
        if code < 0:
            raise ValueError("*code* is < 0.")

        self._exit_code = code
        return None

    def _switch_user(self):
        """
        Switches the *uid* (user id) and *gui* (group id) of the current EMSM
        process to match the expected user defined in the :file:`main.conf`
        configuration file.

        :raises WrongUserError:
            if the rights could not be changed to the target user and group.

        .. seealso::

            * :meth:`emsm.core.conf.Configuration.main`
            * :func:`os.setuid`
            * :func:`os.setgid`
        """
        username = self._conf.main()["emsm"]["user"]

        try:
            user = pwd.getpwnam(username)
        except KeyError as err:
            log.critical(err, exc_info=True)
            raise WrongUserError(username)
            
        group = grp.getgrgid(user.pw_gid)

        try:
            # Switch the group first.
            if os.getegid() != user.pw_gid:
                os.setgid(user.pw_gid)
                log.info("switched gid to '{}' ('{}')."\
                         .format(user.pw_gid, group.gr_name))

            # Switch the user.
            if os.geteuid() != user.pw_uid:
                os.setuid(user.pw_uid)
                log.info("switched uid to '{}' ('{}')."\
                         .format(user.pw_uid, user.pw_name))

        # We failed to switch the user and group.
        except OSError as err:
            log.critical(err, exc_info=True)
            raise WrongUserError(username)
        return None

    def handle_exception(self):
        """
        Checks :func:`sys.exc_info` if there is currently an uncaught exception
        and logs it.
        """
        exc_info = sys.exc_info()

        # Break if there is no exception that is currently handled.
        if None in exc_info:
            return None

        # Log all exceptions
        log.exception("uncaught exception:")

        # Handle the exception by creating a log entry and printing
        # a short error message.
        msg = "EMSM: Uncaught exception:\n"\
              " > Exception: {exc_type}\n"\
              " > Module     {exc_mod}\n"\
              " > Message:   {exc_msg}\n"\
              " > A full traceback can be found in the log file."\
              .format(exc_type = exc_info[0].__name__,
                      exc_mod = traceback.extract_tb(exc_info[2])[-1][0],
                      exc_msg = exc_info[1]
                      )
        msg = termcolor.colored(msg, "red")

        # Don't print the SystemExit exception.
        if not issubclass(exc_info[0], SystemExit):
            print(msg, file=sys.stderr)

        return None

    def setup(self):
        """
        Initialises all components of the EMSM.

        This method will block, until the EMSM filelock could be acquired or
        the configuration timeout value is reached.
        """
        log.info("----------")
        log.info("setting the EMSM {} up ...".format(version.VERSION))

        # Initialise colorama.
        colorama.init()

        # Read the configuration, so that we get to know some startup
        # parameters like the file lock *timeout* or the EMSM user.
        # Note, that the configuration wrappers defines default values for
        # the EMSM. So the configuration files may not exist at this point and
        # we can call ``self._paths.create()`` later.
        self._conf.read()

        # Downgrade the privileges before doing anything else.
        self._switch_user()
        os.chdir(self._paths.instance())

        # Create the EMSM directories.
        # Note, that we must execute this after ``switch_user`` to make sure, the
        # files are owned by the EMSM user.
        self._paths.create()

        # Wait for the file lock to avoid running multiple EMSM applications
        # at the same time.
        log.info("waiting for the file lock ...")

        lock_timeout = self._conf.main()["emsm"].getint("timeout", 0)
        lock_timeout = lock_timeout if lock_timeout > 0 else None
        self._lock.acquire(lock_timeout, 0.05)

        # Now we have the file lock, so we can acquire the emsm.log file.
        self._logger.setup()

        # Reload the configuration again, since it may have changed while
        # waiting for the file lock.
        self._conf.read()

        self._plugins.setup()
        self._plugins.init_plugins()

        self._worlds.load_worlds()

        self._argparser.setup()
        return None

    def run(self):
        """
        Runs the plugins.

        .. seealso::

            * :meth:`emsm.core.plugins.PluginManager.run`
            * :meth:`emsm.core.plugins.PluginManager.finish`
        """
        # Parse the arguments.
        self._argparser.args(cache=False)

        # Dispatch the plugins.
        self._plugins.run()
        self._plugins.finish()

        # Save changes to the configuration that have been made during
        # execution.
        self._conf.write()
        return None

    def finish(self):
        """
        Performs some clean up and background stuff.

        :returns: :meth:`exit_code`

        .. note::

            Do not mix this method up with the
            :meth:`emsm.core.plugins.PluginManager.finish` method. These are not
            related.

        .. seealso::

            * :meth:`run`
            * :meth:`exit_code`
        """
        # Disable colorama.
        colorama.deinit()

        log.info("EMSM finished.")
        self._lock.release()
        return self._exit_code
