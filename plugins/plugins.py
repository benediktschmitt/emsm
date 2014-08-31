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

This is a package manager for EMSM plugins. Uninstall and install plugins with 
this plugin.

This plugin works only with valid packages and plugins that store its data in 
the dedicated paths.

Download
--------

You can find the latest version of this plugin in the EMSM 
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Arguments
---------

.. option:: --install ARCHIVE, -i ARCHIV

    Installs an new plugin from the archive. If a plugin with the same name
    already exists, the installation will fail.    
   
.. option:: --remove PLUGIN, -r PLUGIN

    Removes the plugin from the EMSM. Please make sure, that no other plugin
    depends on this one.
   
.. option:: --doc PLUGIN, -d PLUGIN

    Prints the documentation of the selected plugin.

    .. deprecated:: 2.0.4    
        Use the plugin's ``--long-help`` argument instead:

        .. code-block:: bash

            $ minecraft worlds --long-help
            $ minecraft backups --long-help
            ...

Package structure
-----------------

The archive that contains the plugin should have the following structure:

.. code-block:: none

    |- foo.tar.bz2
       |- plugin.py
       |- data
          |- bar.txt
          |- bar.csv
          |- ...

During the installation, the path names will be changed to:

.. code-block:: none

    |- EMSM_ROOT
      |- plugins
         |- foo.py    <= plugin.py
      |-plugins_data
         |- foo       <= data
            |- bar.txt
            |- bar.csv
            |- ...

If the plugin contains a docstring like this one, it will be printed after
the installation.

Builder
-------

This plugin comes with an EMSM independent building script for new plugins.
This means, that you can call this script without having the EMSM environment.

Arguments
^^^^^^^^^

.. option:: --create TARGET, -c TARGET
.. option:: --source FILE, -s FILE
.. option:: --data DIRECTORY, -d DIRECTORY
.. option:: --help, -h

Example
^^^^^^^

Build the plugin *foo*, that comes with a data directory:

.. code-block:: bash
   
    $ plugin.py -c build/foo -s dev/foo.py -d dev/foo_data
    $ ls build
    ... foo.tar.bz2 ...
"""


# Modules
# --------------------------------------------------
import os
import ast
import shutil
import tempfile
import logging
import argparse
import urllib.request

# local
try:
    from emsm import plugins
    from emsm.base_plugin import BasePlugin
    from emsm.app_lib import userinput
    emsm_context = True    
except ImportError:
    # Not nice, but if I define this dummy class, I can avoid an ugly
    # *if* structure.
    class BasePlugin(object):
        pass
    emsm_context = False


# Backward compatibility
# ------------------------------------------------
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError


# Data and "shortcuts"
# --------------------------------------------------
PLUGIN = "Plugins"
log = logging.getLogger(__name__)


# Exceptions
# --------------------------------------------------
class PluginManagerError(Exception):
    """Base class for all other Exceptions in this module."""


class InstallError(PluginManagerError):
    """Raised if an error occures during the installation."""
    
    
# Data
# --------------------------------------------------
class PluginPackage(object):
    """
    Mangages the installation progess of a new plugin.
    """

    def __init__(self, app, package):
        self.app = app

        # Plugin name
        name = os.path.basename(package)
        name = name[:name.find(".")]
        self.name = name
        
        # Path to the package file
        self.package = package
        
        # Docstring of the package. Available after *install*.
        self.doc = None
        
        self.paths = dict()
        self.paths["plugin"] = os.path.join(
            self.app.paths.plugins_src_dir, self.name) + ".py"
        self.paths["data"] = os.path.join(
            self.app.paths.plugins_data_dir, self.name)

        self._installed = False
        return None

    @property
    def installed(self):
        return self._installed

    def install(self):
        """
        Unpacks the archive with the plugin and moves the files and
        folders to the application's directories.

        Raises: InstallError
        """
        if self._installed:
            return None

        log.info("Installing the plugin: {}".format(self.name))
        
        # Check if the plugin already exists.
        if self.app.plugins.plugin_is_available(self.name):
            msg = "A plugin with the same name has already been installed."
            log.error(msg)
            raise InstallError(msg)

        # Extract the plugin in a temporary directory so that the plugin will
        # not mess up the application's directories if it's not valid.
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                shutil.unpack_archive(
                    filename = self.package,
                    extract_dir = temp_dir
                    )
            except (ValueError, shutil.ReadError, FileNotFoundError) as error:
                msg = "The archive could not be unpacked: {}".format(error)
                log.error(msg)
                raise InstallError(msg)

            # Check the files and directories in the temporary directory.
            package_paths = {filename: os.path.join(temp_dir, filename) \
                             for filename in os.listdir(temp_dir)}
            
            if "plugin.py" not in package_paths:
                msg = "The package does not contain the 'plugin.py' file."
                log.error(msg)
                raise InstallError(msg)
            
            if not os.path.isfile(package_paths["plugin.py"]):
                msg = "'plugin.py' is not a file."
                log.error(msg)
                raise InstallError(msg)

            if "data" in package_paths \
               and not os.path.isdir(package_paths["data"]):
                msg = "'data' is not a directory."
                log.error(msg)
                raise InstallError(msg)

            # Move the files.
            shutil.move(package_paths["plugin.py"], self.paths["plugin"])
            if "data" in package_paths:
                shutil.move(package_paths["data"], self.paths["data"])

        # Extract the docstring from the plugin.
        with open(self.paths["plugin"]) as file:
            ast_node = ast.parse(file.read())
            try:
                self.doc = ast.get_docstring(ast_node)
            except TypeError:
                pass
            
        log.info("Installation complete.")
        self._installed = True
        return None

    def print_doc(self):
        """Prints the documentation of the plugin if available."""
        if self.doc is not None:
            print(self.doc)
        else:
            print("<Doc not available>")
        return None

    def load_plugin(self):
        """Loads the plugin."""
        if self._installed:
            try:
                self.app.plugins.import_plugin(self.paths["plugin"])
            except plugin_manager.PluginException as err:
                log.error(err)
                raise
        return None

    def ui_install(self):
        """
        Provides a user interface for the installation.
        """
        print("Installing {} ...".format(self.name))
        
        try:
            self.install()
        except InstallError as err:
            print("> An error occured during the installation.")
            print("> {}".format(err))
        else:
            if userinput.ask("Do you want to read the documentation?", True):
                self.print_doc()

            if userinput.ask("Do you want to load the plugin now?", False):
                try:
                    self.load_plugin()
                except plugin_manager.PluginException as err:
                    print("> An error occured while loading the plugin:")
                    print("> {}".format(err))

            print("Installation complete.")
        return None


class Plugins(BasePlugin):
    """
    Provides methods to install or remove plugins for this application.
    """

    version = "2.0.0"
    
    def __init__(self, app, name):
        BasePlugin.__init__(self, app, name)

        # Argparser
        self.argparser.description = (
            "This plugin provides methods to install or remove plugins from "
            "this application.")
        
        self.argparser.add_argument(
            "-i", "--install",
            action = "store",
            dest = "install",
            metavar = "ARCHIVE",
            help = "Installs the plugin from the archive."
            )
        self.argparser.add_argument(
            "-r", "--remove",
            action = "store",
            dest = "remove",
            metavar = "PLUGIN",
            choices = self.app.plugins.get_plugin_names(),            
            help = "Removes the plugin from the EMSM."
            )

##        self.argparser.add_argument(
##            "-u", "--update",
##            action = "append",
##            dest = "update",
##            metavar = "PLUGIN",
##            choices = self.app.plugins.get_plugin_names(),
##            help = "Tries to update the plugin, if a new version is available."
##            )
##        self.argparser.add_argument(
##            "-U", "--update-all",
##            action = "count",
##            dest = "update_all",
##            help = "Updates all plugins."
##            )
        
        self.argparser.add_argument(
            "-d", "--doc",
            action = "store",
            dest = "print_doc",
            metavar = "PLUGIN",
            choices = self.app.plugins.get_plugin_names(),
            help = "Prints the docstring of the plugin."
            )
        return None

    def run(self, args):
        # I did not like the installation progress coded in the plugin_manager,
        # so we need this handler.
        if args.install:
            package = PluginPackage(self.app, args.install)
            package.ui_install()

        # We have nothing to do here. The EMSM performs a clean uninstallation
        # itself.
        if args.remove:
            self.app.plugins.uninstall(args.remove)

        if args.print_doc:
            plugin_module = self.app.plugins.get_module(args.print_doc)
            if plugin_module:
                print("{} - documentation:".format(args.print_doc))
                print(plugin_module.__doc__)

##        # Update plugins if possible.
##        if args.update or args.update_all:
##            if args.update_all:
##                plugins = self.app.plugins.get_all_plugins()
##            else:
##                plugins = [self.app.plugins.get_plugin(p)\
##                           for p in args.update]
##            
##            for p in plugins:
##                p.update()
        return None


# Main
# ------------------------------------------------
if __name__ == "__main__":
    # Parse the command line args.
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--create", required=True,
                        help="The target of the plugin package.")
    parser.add_argument("-s", "--source", required=True,
                        help="The source file of the plugin.")
    parser.add_argument("-d", "--data",
                        help="The data directory, that should be included.")
    args = parser.parse_args()

    # Create the archive
    with tempfile.TemporaryDirectory() as temp_dir:
        print("copying the plugin")
        shutil.copy(args.source, os.path.join(temp_dir, "plugin.py"))
        if args.data:
            print("copying the data folder")
            shutil.copytree(args.data, os.path.join(temp_dir, "data"))

        archive = shutil.make_archive(
            args.create[:args.create.find(".")], "bztar", temp_dir, "./")
        print("packed in:", archive)
