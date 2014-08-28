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
import os
import sys
import getpass

# local
import argparse_wrapper
import base_plugin
import configuration
import logging_wrapper
import pathsystem
import plugin_manager
import server_wrapper
import world_wrapper
from app_lib import file_lock


# Data
# ------------------------------------------------
__all__ = ["ApplicationException", "WrongUserError",
           "Application"]


_LICENSE = """The MIT License (MIT)

Copyright (c) 2014 Benedikt Schmitt <benedikt@benediktschmitt.de>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


# Exceptions
# ------------------------------------------------
class ApplicationException(Exception):    
    """
    Base class for all exceptions in this module.
    """
    pass


class WrongUserError(ApplicationException):    
    """
    Raised if the script is called from another
    user than declared in the configuration.
    """

    def __init__(self, required_user):
        self.required_user = required_user
        return None

    def __str__(self):
        temp = "This script requires a user named '{}'. "\
               "The current user is '{}'."\
               .format(self.required_user, getpass.getuser())
        return temp

    
# Classes
# ------------------------------------------------
class Application(object):    
    """
    This class sets the application up and manages the run.
    """

    version = "2.0.4-beta"

    license = _LICENSE

    def __init__(self):
        
        # Do not change the order of the construction!
        # \Independent constructions and primary ressources
        self.paths = pathsystem.Pathsystem()
        self.lock = file_lock.FileLock(
            os.path.join(self.paths.emsm_dir, "app.lock"))
        self._logger = logging_wrapper.Logger(self)
        self.log = self._logger.emsm

        # \Input
        self.conf = configuration.Configuration(self)
        self.argparser = argparse_wrapper.ArgumentParser(self)

        # \Wrapper and manager
        self.worlds = world_wrapper.WorldManager(self)
        self.server = server_wrapper.ServerManager(self)
        self.plugins = plugin_manager.PluginManager(self)
        return None

    # Common    
    # ------------------------------------------------

    def _check_user(self):
        """
        Raises WrongUserError if the user that is running this
        script is not the user named in the configuration file.
        """
        required_user = self.conf.main["emsm"]["user"]
        if getpass.getuser() != required_user:
            raise WrongUserError(required_user)
        return None
    
    # Runlevel    
    # ------------------------------------------------
    
    def setup(self):
        """
        Sets the application up.
        """
        # Reading the conf is ok. We're not writing to it.
        self.conf.read()
        
        # Everything seems ok, so get ready to run.
        # We need to acquire the file lock, to avoid that different instances
        # of the emsm access the same resources. This includes the logfile.
        lock_timeout = self.conf.main["emsm"].getint("timeout", None)
        if lock_timeout == -1:
            lock_timeout = None
        self.lock.acquire(lock_timeout, 0.1)

        # Set the logger up as early as possible, so that we can log any errors.
        # The only exceptions, that can not be logged, are the TimeoutException
        # of the file lock.
        self._logger.setup()        
        self.conf.read()
        self._logger.load_conf()

        # Todo: I don't like logging so late...
        self.log.info("EMSM - Setup")
        
        self._check_user()
        self.argparser.add_app_args()

        # Wrappers
        self.server.load_server()
        self.worlds.load()

        # Plugins
        self.plugins.import_from_app_plugin_dir()
        self.plugins.init_plugins()

        # Because all plugin subparsers are not set up, we can parse all
        # arguments.
        self.argparser.parse_args()
        return None

    def run(self):
        """
        Dispatch the application.
        """
        self.plugins.run()
        self.plugins.finish()
        return None

    def finish(self):
        """
        For clean up and background stuff.
        """
        try:
            self.conf.write()
        finally:
            self.log.info("EMSM - End")
            self._logger.shutdown()
            self.lock.release()
        return None

    # Application context
    # --------------------------------------------
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if not (exc_type is None or isinstance(exc_value, SystemExit)):
            msg = ("EMSM: Critical:\n"
                   " > Exception: {exc_type}\n"
                   " > Message:   {exc_value}\n"
                   " > A full traceback can be found in the log file."
                   )
            msg = msg.format(exc_type=exc_type.__name__,
                             exc_value=exc_value)
            print(msg, file=sys.stderr)
            self.log.critical("Uncaught exception:", exc_info=True)

        self.finish()
        return None
    

# Main
# ------------------------------------------------
if __name__ == "__main__":
    # The application will log all errors and controll
    # the work flow. Any traceback output will be surpressed and logged.
##    try:
        with Application() as app:
            app.setup()
            app.run()
##    except:
##        pass

