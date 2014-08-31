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

# std
import os
import logging
import shutil
import argparse
import subprocess

# local
from . import argparse_
from .app_lib import userinput


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
    INIT_PRIORITY = 0

    # Integer with the finish priority of the plugin.
    # A higher value results in a later call of the finish method.
    FINISH_PRIORITY = 0

    # The last compatible version of the application the
    # plugin worked.
    VERSION = "0.0.0"

    # The plugin manager can lookup there for a new version of the plugin.
    DOWNLOAD_URL = ""

    # This string is like the man page of the plugin and displayed when
    # invoking the plugin with the *--long-help* command. Per default,
    # we use the docstring of the module that contains the plugin. Therefore,
    # it is first available, when at least one plugin has been initialised.
    DESCRIPTION = ""

    def __init__(self, app, name):
        """
        Initialises the configuration and the storage of the plugin.

        Creates the following attributes:
            * self.app
            * self.name
            * self.log
            * self.conf
            * self.data_dir
            * self.argparser

        Extend but do not overwrite.
        """
        self.app = app
        self.name = name
        self.log = logging.getLogger(name)

        # Set the configuration up.
        main_conf = app.conf.main()
        if name not in main_conf:
            main_conf.add_section(name)
        self.conf = main_conf[name]

        # Get the directories of the plugin.
        self.data_dir = app.paths.plugin_data_dir(name)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Get the docstring of the plugin module.
        type(self).description = app.plugins.get_module(name).__doc__

        # Create a new argparser for this plugin.
        self.argparser = app.argparser.plugin_parser(name)
        
        self.argparser.add_argument(
            "--long-help",
            action = argparse_.LongHelpAction,
            description = self.description)
        return None

    def uninstall(self):
        """
        Called if the plugin should be uninstalled. It should
        remove all files and configuration options that it made.

        Raises: KeyboardInterrupt when the user aborts the uninstallation.
        """        
        if not userinput.ask("Do you really want to remove this plugin?"):
            # I did not want to implement a new exception type for this case.
            # I think KeyboardInterrupt is good enough.
            raise KeyboardInterrupt

        real_module = self.app.plugins.get_module(self.name)
        if real_module:
            os.remove(real_module.__file__)
        
        if userinput.ask("Do you want to remove the data directory?"):
            shutil.rmtree(self.data_dir, True)
            
        if userinput.ask("Do you want to remove the configuration?"):
            self.app.conf.main.remove_section(self.name)
        return True


    # EMSM plugin runlevel
    # --------------------------------------------

    def embedded_run(self, args):
        """
        Can be called from other plugins, if they want to use a plugins feature.
        args is a string, that contains the parameters of the plugin.    
        """
        args = self.argparser.parse_args(args.split())
        self.run(args)
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

    def finish(self):
        """
        Called after the run method, but this time for all plugins.

        Can be used for clean up stuff or background jobs.
        """
        return None
