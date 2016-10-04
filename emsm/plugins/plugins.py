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

.. option:: --install ARCHIVE

    Installs an new plugin from the archive. If a plugin with the same name
    already exists, the installation will fail.

.. option:: --remove PLUGIN

    Removes the plugin from the EMSM. Please make sure, that no other plugin
    depends on this one.

.. option:: --list

    Lists all loaded plugins.


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

Builder
-------

This plugin comes with an EMSM independent building script for new plugins.
This means, that you can call this script without having the EMSM environment.

Arguments
^^^^^^^^^

.. option:: --create TARGET
.. option:: --source FILE
.. option:: --data DIRECTORY
.. option:: --help, -h

Example
^^^^^^^

Build the plugin *foo*, that comes with a data directory:

.. code-block:: bash

    $ plugin.py --create build/foo --source dev/foo.py --data dev/foo_data
    $ ls build
    ... foo.tar.bz2 ...
"""


# Modules
# --------------------------------------------------

# std
import os
import shutil
import tempfile
import logging
import argparse

# third party
import termcolor

# local
try:
    import emsm
    from emsm.core.base_plugin import BasePlugin
    emsm_context = True
except ImportError:
    BasePlugin = object
    emsm_context = False


# Backward compatibility
# ------------------------------------------------

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError


# Data
# --------------------------------------------------

PLUGIN = "Plugins"

log = logging.getLogger(__file__)


# Exceptions
# --------------------------------------------------

class PluginManagerError(Exception):
    """
    Base class for all other Exceptions in this module.
    """


class PluginInstallError(PluginManagerError):
    """
    Raised if an error occures during the installation.
    """


class PluginAlreadyInstalledError(PluginInstallError):
    """
    Raised if a plugin should be installed that would
    overwrite another plugin that is already installed.
    """

class PluginPackageCorruptedError(PluginInstallError):
    """
    Raised if a plugin package could not be installed
    because it has an invalid structure.
    """


# Data
# --------------------------------------------------

class PluginInstaller(object):
    """
    Installs a new plugin to the EMSM.
    """

    def __init__(self, app, archive_path):
        """
        """
        self._app = app

        # The path to the plugin archive.
        self._archive_path = archive_path

        # The name of the plugin.
        name = os.path.basename(archive_path)
        name = name[:name.find(".")]
        self._name = name

        # Methods to undo the installation progress. If a installation
        # part is complete, the method to undo this "part" is appended
        # to this list, so that we can call the *undo* functions in the
        # correct order.
        self._undo_func = list()
        return None

    def archive_path(self):
        """
        Returns the path to the archive that contains the plugin that should be
        installed.
        """
        return self._archive_path

    def plugin_name(self):
        """
        Returns the *name* of the plugin.
        """
        return self._name

    def _install_plugin_module(self, package_path):
        """
        Installs the *plugin.py* module in *package_path* into the main
        plugin directory of the EMSM and renames it.

        See also:
            * name()
        """
        package_module_path = os.path.join(package_path, "plugin.py")

        # Check if the plugin module exists.
        if not os.path.exists(package_module_path):
            raise PluginPackageCorruptedError(
                "the package does not contain a *plugin.py* file."
                )

        # Check if it is a file.
        if not os.path.isfile(package_module_path):
            raise PluginPackageCorruptedError(
                "the *plugin.py* file in the package is NOT a file."
                )

        # Copy the plugin.py file to the EMSM *plugins* directory.
        emsm_module_path = os.path.join(
            self._app.paths().plugins_dir(), self._name + ".py"
            )
        shutil.move(package_module_path, emsm_module_path)

        # Add the undo function.
        self._undo_func.append(self._undo_plugin_module)
        return None

    def _undo_plugin_module(self):
        """
        Removes the plugin module previously installed with
        ``_install_plugin_module()``.
        """
        emsm_module_path = os.path.join(
            self._app.paths().plugins_dir(), self._name + ".py"
            )
        try:
            os.remove(emsm_module_path)
        except OSError:
            # We can't do anything ...
            pass
        return None

    def _install_plugin_data(self, package_path):
        """
        Copies the *data* directory from *package_path* to the EMSM
        plugins_data directory and renames it.

        See also:
            * name()
        """
        package_data_dir = os.path.join(package_path, "data")
        emsm_data_dir = self._app.paths().plugin_data_dir(self._name)

        # Check if the package contains a data directory.
        if not os.path.exists(package_data_dir):
            # Break, since the data directory is not required..
            return None

        # Check if the data directory is a *directory*.
        if not os.path.isdir(package_data_dir):
            raise PluginPackageCorruptedError(
                "the *data* directory in the package is NOT a directory."
                )

        # Make sure there is no directory for this plugin in EMSM_ROOT/plugins_data.
        if os.path.exists(emsm_data_dir):
            raise PluginInstallError(
                "the EMSM contains already a plugin directory for '{}'."\
                .format(self._name)
                )

        # Move the data directory to the EMSM *plugins_data* directory.
        shutil.move(package_data_dir, emsm_data_dir)

        # Add the undo function.
        self._undo_func.append(self._undo_plugin_data)
        return None

    def _undo_plugin_data(self):
        """
        Removes the plugin data directory previously installed with
        ``_install_plugin_data_dir()``.
        """
        try:
            shutil.rmtree(self._app.paths().plugin_data_dir(self._name))
        except OSError:
            # We can't do anything ...
            pass
        return None

    def _undo(self):
        """
        Undos all installation steps done till now.
        """
        for func in reversed(self._undo_func):
            func()
        return None

    def _install(self):
        """
        The raw installation progress, that might throw some exceptions.

        Exceptions:
            * PluginInstallError
            * PluginPackageCorruptedError
            * PluginAlreadyInstalledError
        """
        self._undo_func = list()

        # Check if there is already a plugin with that name.
        if self._app.plugins().plugin_is_available(self._name):
            raise PluginAlreadyInstalledError(
                "the plugin '{}' is already installed.".format(self._name)
                )

        # Unpack the archive in a temporary folder.
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                shutil.unpack_archive(
                    filename = self._archive_path,
                    extract_dir = tmp_dir
                    )
            except (ValueError, FileNotFoundError, shutil.ReadError) as err:
                raise PluginInstallError(
                    "the plugin archive '{}' could not be uncompressed."\
                    .format(self._name)
                    )
            else:
                try:
                    self._install_plugin_module(tmp_dir)
                    self._install_plugin_data(tmp_dir)
                except:
                    self._undo()
                    raise
        return None

    def install(self):
        """
        Like *_install()*, but catches the exceptions, prints the progress and
        creates more log entries.
        """
        print("package_path: {}".format(self._archive_path))
        print("package_name: {}".format(self._name))
        print("installing package ...")

        log.info("installing '{}' from '{}' ..."\
                 .format(self._name, self._archive_path)
                 )

        try:
            self._install()
        except PluginAlreadyInstalledError as err:
            print(termcolor.colored("error:", "red"),
                  "a plugin with the name '{}' is already installed."\
                  .format(self._name)
                  )
            log.error(err)
        except PluginPackageCorruptedError as err:
            print(termcolor.colored("error:", "red"),
                  "the package is not a valid plugin package."
                  )
            log.error(err)
        except PluginInstallError as err:
            print(termcolor.colored("error:", "red"), err)
            log.error(err)
        else:
            print("installation complete.")
            log.info("installation of '{}' complete.".format(self._name))
        return None


class Plugins(BasePlugin):

    VERSION = "5.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, app, name):
        """
        """
        BasePlugin.__init__(self, app, name)

        self._setup_argparser()
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()
        parser.description = "Install and remove EMSM plugins"

        # We want to allow only one action per run.
        me_group = parser.add_mutually_exclusive_group()

        me_group.add_argument(
            "--install",
            action = "store",
            dest = "plugins_install",
            metavar = "ARCHIVE",
            help = "Install a new plugin from the given archive."
            )

        # Get the names of all loaded plugins, excluding THIS plugin
        # (the plugins.py plugin).
        plugin_names = [name \
                        for name in self.app().plugins().get_plugin_names()
                        if name != self.name()]
        me_group.add_argument(
            "--uninstall",
            action = "store",
            dest = "plugins_uninstall",
            metavar = "PLUGIN",
            choices = plugin_names,
            help = "Uninstall the plugin."
            )

        me_group.add_argument(
            "--list",
            action = "count",
            dest = "plugins_list",
            help = "Lists all loaded plugins."
            )
        return None

    def run(self, args):
        """
        """
        if args.plugins_install:
            installer = PluginInstaller(self.app(), args.plugins_install)
            installer.install()

        elif args.plugins_uninstall:
            plugin = self.app().plugins().get_plugin(args.plugins_uninstall)
            plugin.uninstall()

        elif args.plugins_list:
            self._list_plugins()
        return None

    def _list_plugins(self):
        """
        Lists all loaded plugins.
        """
        # We list the plugins in alphabetical order.
        plugins = self.app().plugins().get_plugin_names()
        plugins.sort()

        if not plugins:
            print("- no plugins loaded -")
        else:
            for name in plugins:
                print("* {}".format(name))
        return None


# Main
# ------------------------------------------------

if __name__ == "__main__":

    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create",
        required = True,
        help = "The target location of the packed archive."
        )
    parser.add_argument(
        "--source",
        required = True,
        help = "The source file of the plugin."
        )
    parser.add_argument(
        "--data",
        help = "The data directory, that should be included."
        )
    args = parser.parse_args()

    # Create the archive
    with tempfile.TemporaryDirectory() as temp_dir:

        # Copy the plugin module and the data directory to the temp_dir.
        print("copying plugin module ...")
        shutil.copy(args.source, os.path.join(temp_dir, "plugin.py"))

        if args.data:
            print("copying plugin data dir ...")
            shutil.copytree(args.data, os.path.join(temp_dir, "data"))

        # Create the archive by zipping the temp_dir.
        print("compressing archive ...")
        archive = shutil.make_archive(
            base_name = args.create,
            format = "bztar",
            root_dir = temp_dir,
            base_dir = "./"
            )
        print("created '{}'.".format(archive))
