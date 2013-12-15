#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


# Modules
# ------------------------------------------------
import os
import sys
import getpass

# local
import argparse_wrapper
import base_plugin
import configuration
import eventsystem
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
        temp = "This script requires a user named '{}'."\
               .format(self.required_user)
        return temp

    
# Classes
# ------------------------------------------------
class Application(object):    
    """
    This class sets the application up and manages the run.
    """

    version = "2.0.0-beta"

    def __init__(self):
        
        # Do not change the order of the construction!
        # \Independent constructions and primary ressources
        self.paths = pathsystem.Pathsystem()
        self.lock = file_lock.FileLock(
            os.path.join(self.paths.emsm_dir, "app.lock"))
        self.events = eventsystem.Dispatcher()
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
        self.lock.acquire()
        
        # Input
        self.conf.read()
        self._check_user()
        self._logger.load_conf()
        self.argparser.add_app_args()

        # Wrappers
        self.server.load()
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
        return None

    def finish(self):
        """
        For clean up and background stuff.
        """
        try:
            self.plugins.finish()
            self.conf.write()
        finally:
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
        return None
    

# Main
# ------------------------------------------------
if __name__ == "__main__":
    # The application will log all errors and controll
    # the work flow. Any traceback output will be surpressed and logged.
    try:
        with Application() as app:
            app.setup()
            app.run()
            app.finish()
    except:
        pass
