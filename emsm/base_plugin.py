#!/usr/bin/env python3


# Modules
# ------------------------------------------------
import os
import shutil


# Data
# ------------------------------------------------
__all__ = ["BasePlugin"]


# Classes
# ------------------------------------------------
class BasePlugin(object):
    """
    This is the base class for all plugins.

    The dispatcher will call the methods when
    they are needed.
    """

    # Integer with the init priority of the plugin.
    # A higher value results in a later initialisation.
    init_priority = 0

    # Integer with the finish priority of the plugin.
    # A higher value results in a later call of the finish method.
    finish_priority = 0

    # The last compatible version of the application the
    # plugin worked.
    version = "0.0.0"

    def __init__(self, application, name):
        """
        Initialises the configuration and the storage of the plugin.

        Creates the following attributes:
            * self.application
            * self.name
            * self.conf
            * self.data_dir

        Extend but do not overwrite.
        """
        self.application = application
        self.name = name

        # Set the configuration up.
        main_conf = application.configuration.main
        if name not in main_conf:
            main_conf.add_section(name)
        self.conf = main_conf[name]

        # Get the directories of the plugin.
        pathsystem = application.pathsystem
        self.data_dir = pathsystem.get_plugin_data_dir(name)

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        return None

    def uninstall(self):
        """
        Called if the plugins should be uninstalled. It should
        remove all files and configuration options that it made.
        """
        return None

    # run (only called, if the plugin is invoked)
    # --------------------------------------------
    
    def setup_argparser_argument_group(self, group):
        """
        Called from the dispatcher if the plugin is invoked.

        The plugin should add it's method to the argparser
        argument group in this method.
        """
        return None

    def run(self, args):
        """
        Called from the dispatcher if the plugin is invoked and
        the application is ready to run.

        Consider this method as the main method of the plugin.

        args is an argparse.Namespace instance that contains the values
        of the parsed arguments of the argparser.
        """
        return None

    # end
    # --------------------------------------------
    
    def finish(self):
        """
        Called after the run method, but this time for all plugins.

        Can be used for clean up stuff.
        """
        return None
