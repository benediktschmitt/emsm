#!/usr/bin/env python3


# Modules
# ------------------------------------------------
import sys
import getpass
import traceback
import os

# local
import argparse_
import configuration
import eventsystem
import pathsystem
import server_wrapper
import world_wrapper
import plugin_manager
import server_manager
import world_manager
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
    This class sets the application up and manages
    the run.
    """

    version = "1.0.0"

    def __init__(self):
        
        # Do not change the order of the initialisation!
        self.pathsystem = pathsystem.Pathsystem()
        
        self.lock = file_lock.FileLock(
            os.path.join(self.pathsystem.emsm_source_dir, "app.lock"))

        self.configuration = configuration.Configuration(
            self.pathsystem.configuration_dir)
        self.argparser = argparse_.ArgumentParser()

        self.event_dispatcher = eventsystem.Dispatcher()

        self.plugin_manager = plugin_manager.PluginManager(self)
        self.world_manager = world_manager.WorldManager(self)
        self.server_manager = server_manager.ServerManager(self)
        return None
    
    def _check_user(self):
        """
        Raises WrongUserError if the user that is running this
        script is not the user named in the configuration file.
        """
        required_user = self.configuration.main["emsm"]["user"]
        
        if getpass.getuser() != required_user:
            raise WrongUserError(required_user)
        return None
    
    def setup(self):
        """
        Sets the application up.
        """
        self.configuration.read()
        self._check_user()

        self.server_manager.load_server()
        self.world_manager.load_worlds()
        self.plugin_manager.import_from_app_plugin_dir()

        self.argparser.add_application_args(
            self.world_manager.get_available_worlds(),
            self.plugin_manager.get_available_plugins(),
            self.version
            )
        self.argparser.parse_known_args()

        self.plugin_manager.init_plugins()
        self.plugin_manager.prepare_run()

        self.argparser.parse_args()
        return None

    def run(self):
        """
        Dispatch the application.
        """
        self.plugin_manager.run()
        return None

    def finish(self):
        """
        For clean up stuff.
        """
        self.plugin_manager.finish()
        self.configuration.write()
        return None

    # application context
    # --------------------------------------------

    def __enter__(self):
        self.lock.acquire()
        return self


    def __exit__(self, exc_type, exc_value, tb):
        try:
            # XXX: I think using the logging module
            # would be fine.
            if isinstance(exc_value, SystemExit):
                pass
            elif exc_type is not None:
                # Stdout
                print("application: failure:")
                print("\t{}: {}".format(exc_type.__name__, exc_value))
                # Error file
                error_file = os.path.join(
                    self.pathsystem.emsm_source_dir, "errors.txt")
                with open(error_file, "a") as error_file:
                    print(sys.argv, file=error_file)
                    traceback.print_tb(tb, file=error_file)
                    print("-"*80, file=error_file)
        finally:
            self.lock.release()
        return None


# Main
# ------------------------------------------------
if __name__ == "__main__":
    # I think it's convenient to handle the
    # locking meachnism and the exceptions this way.
    try:
        with Application() as app:
            app.setup()
            app.run()
            app.finish()
    except:
        pass
