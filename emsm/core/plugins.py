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
import sys
import logging
import importlib.machinery

# third party
import blinker

# local
from .version import VERSION
from .base_plugin import BasePlugin


# Backward compatibility
# ------------------------------------------------

if hasattr(importlib.machinery, "SourceFileLoader"):
    def _import_module(name, path):
        loader = importlib.machinery.SourceFileLoader(name, path)
        return loader.load_module()
else:
    import imp
    _import_module = imp.load_source
    del imp


# Data
# ------------------------------------------------

__all__ = [
    "PluginException",
    "PluginImplementationError",
    "PluginOutdatedError",
    "PluginManager",
    ]

log = logging.getLogger(__file__)


# Exceptions
# ------------------------------------------------

class PluginException(Exception):
    """
    Base class for all exceptions in this module.
    """
    pass


class PluginImplementationError(PluginException):
    """
    Raised if a plugin is not correct implemented.
    """

    def __init__(self, plugin, msg):
        self.plugin = plugin
        self.msg = msg
        return None

    def __str__(self):
        temp = "The plugin '{}' is not correct implemented. {}"\
               .format(self.plugin, self.msg)
        return temp


class PluginOutdatedError(PluginException):
    """
    Raised if the version of the plugin is not compatible with
    the EMSM version.

    .. seealso::

        * http://semver.org/
    """

    def __init__(self, plugin):
        self.plugin = plugin
        return None

    def __str__(self):
        temp = "The plugin '{}' is outdated.".format(self.plugin)
        return temp


# Classes
# ------------------------------------------------

class PluginManager(object):
    """
    Loads and manages all plugins.

    If you want to write a plugin and search for the docs, take a look at the
    :mod:`~emsm.plugins.hellodolly` plugin.

    .. seealso::

        * :class:`~emsm.core.base_plugin.BasePlugin`
    """

    def __init__(self, app):
        """
        """
        self._app = app

        # Maps the module name to the module object.
        self._plugin_modules = dict()

        # Maps the module name to the plugin class.
        self._plugin_types = dict()

        # Maps the module name to the plugin instance.
        self._plugins = dict()

        # Unload the plugin when it has been uninstalled.
        #
        # See also:
        #   * BasePlugin.uninstall()
        BasePlugin.plugin_uninstalled.connect(self._uninstall)
        return None

    def get_module(self, plugin_name):
        """
        Returns the Python module object that contains the plugin with the
        name *plugin_name* or ``None`` if there is no plugin with that name.
        """
        return self._plugin_modules.get(plugin_name)

    def get_plugin_type(self, plugin_name):
        """
        Returns the plugin class for the plugin with the name *plugin_name* or
        ``None``, if there is no plugin with that name.
        """
        return self._plugin_types.get(plugin_name)

    def plugin_is_available(self, plugin_name):
        """
        Returns ``True``, if the plugin with the name *plugin_name* is
        available.
        """
        return plugin_name in self._plugin_modules

    def get_plugin_names(self):
        """
        Returns the names of all loaded plugins.
        """
        return list(self._plugin_modules.keys())

    def get_plugin(self, plugin_name):
        """
        Returns the instance of the plugin with the name *plugin_name* that is
        currently loaded and used by the EMSM.
        """
        return self._plugins.get(plugin_name)

    def get_all_plugins(self):
        """
        Returns all currently loaded plugin instances.

        .. seealso::

            * :meth:`get_plugin_names`
            * :meth:`get_plugin`
        """
        return self._plugins.values()

    def _plugin_is_outdated(self, plugin):
        """
        Returns ``True`` if the *plugin* is outdated and not compatible with
        the current EMSM version.

        .. seealso::

            * :mod:`emsm.core.version`
            * http://semver.org
        """
        app_version = VERSION.split(".")
        plugin_version = plugin.VERSION.split(".")

        # The version number is invalid.
        if len(plugin_version) < 2:
            return True
        # Only a change in the major version number means a break
        # with the API.
        elif app_version[0] != plugin_version[0]:
            return True
        else:
            return False

    def import_plugin(self, path):
        """
        Loads the plugin located at *path*.

        .. note::

            The *path* is no longer added to :attr:`sys.path` (EMSM Vers. >= 3).

        :raises PluginOutdatedError:
            when the plugin is outdated.
        :raises PluginImplementationError:
            when the plugin is not correct implemented.

        .. seealso::

            * :meth:`_plugin_is_outdated`
        """
        # The module name is the name of the plugin.
        # I assume, that a modulename always ends with '.py'.
        name = os.path.basename(path)
        name = name[:-3]

        # Try to import the module.
        try:
            module = _import_module(name, path)
        except Exception as err:
            raise PluginImplementationError(name, err)

        # Check if the module contains a plugin.
        if not hasattr(module, "PLUGIN"):
            msg = "The gloabal 'PLUGIN' variable is not defined."
            raise PluginImplementationError(name, msg)

        if not hasattr(module, module.PLUGIN):
            msg = "The plugin module '{}' does not contain the declared "\
                  "plugin class '{}'".format(name, module.PLUGIN)
            raise PluginImplementationError(name, msg)

        # Get the plugin class.
        plugin_type = getattr(module, module.PLUGIN)

        # The plugin has to be a subclass of BasePlugin.
        if not issubclass(plugin_type, BasePlugin):
            msg = "The plugin '{}' is not a subclass of BasePlugin."\
                  .format(module.PLUGIN)
            raise PluginImplementationError(name, msg)

        # Check if the plugin is tested and compatible with the current
        # EMSM version.
        if self._plugin_is_outdated(plugin_type):
            raise PluginOutdatedError(name)

        # Save the plugin module and class.
        # A plugin instance is created later, when it is first needed.
        self._plugin_modules[name] = module
        self._plugin_types[name] = plugin_type
        return None

    def import_from_directory(self, directory):
        """
        Imports all Python modules in the :file:`directory`.

        Files that do not contain a valid EMSM plugin, are ignored. You can
        check the log files to see which plugins have been ignored.

        .. seealso::

            * :meth:`import_plugin`
        """
        def file_is_plugin(path):
            """
            Returns ``True`` if the path probably points to a plugin module.
            """
            filename = os.path.basename(path)
            if os.path.isdir(path):
                return False
            elif filename.startswith("_"):
                return False
            elif not filename.endswith(".py"):
                return False
            elif filename.count(".") != 1:
                return False
            return True

        log.info("loading plugins from '{}' ...".format(directory))

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if not file_is_plugin(path):
                continue

            try:
                self.import_plugin(path)
            except PluginImplementationError as err:
                log.warning(err)
            except PluginOutdatedError as err:
                log.warning(err)
            else:
                log.info("loaded plugin from '{}'.".format(path))
        return None

    def remove_plugin(self, plugin_name, call_finish=False):
        """
        Unloads the plugin with the name *plugin_name*.

        :param str plugin_name:
            The name of the plugin that should be unloaded.
        :param bool call_finish:
            If true, the :meth:`~emsm.core.base_plugin.BasePlugin.finish`
            method of the plugin is called, before it is unloaded.
        """
        log.info("unloading plugin '{}' ...".format(plugin_name))

        plugin = self._plugins.get(plugin_name, None)

        # Break if there is not plugin with that name.
        if plugin is None:
            return None

        if call_finish:
            plugin.finish()

        # Remove the plugin.
        del self._plugins[plugin_name]
        del self._plugin_types[plugin_name]
        del self._plugin_modules[plugin_name]

        # The plugin has been removed.
        log.info("the plugin '{}' has been unloaded.".format(plugin_name))
        return None

    def _uninstall(self, plugin):
        """
        Called, when the plugin has been uninstalled.

        .. seealso::

            * :attr:`emsm.core.base_plugin.BasePlugin.plugin_uninstalled`
        """
        # Break if we do not own this plugin.
        if not plugin in self._plugins.values():
            return None

        # Unload the plugin.
        self.remove_plugin(plugin_name=plugin.name(), call_finish=False)
        return None

    def setup(self):
        """
        Imports all plugins from the application's plugin directory.

        .. seealso::

            * :meth:`emsm.core.paths.Pathsystem.plugins`
            * :meth:`emsm.core.paths.Pathsystem.emsm_plugins`
        """
        paths = self._app.paths()
        self.import_from_directory(paths.emsm_plugins())
        self.import_from_directory(paths.plugins())
        return None

    def init_plugins(self):
        """
        Creates a plugin instance for each loaded plugin class.

        When you call this method multiple times, only plugins that have
        not been initialised already, will be initialised.
        """
        log.info("initialising plugins ...")

        # Initialise the plugins corresponding to their *INIT_PRIORITY*
        init_queue = self._plugin_types.items()
        init_queue = sorted(init_queue, key=lambda e: e[1].INIT_PRIORITY)

        for name, plugin_type in init_queue:

            # The plugin has already been initialised.
            if name in self._plugins:
                continue

            # Create a new plugin instance and save it.
            plugin = plugin_type(self._app, name)
            self._plugins[name] = plugin

        log.info("initialised plugins.")
        return None

    def run(self):
        """
        Calls :meth:`~emsm.core.base_plugin.BasePlugin.run` of the plugin that
        has been selected by the command line arguments.

        .. seealso::

            * :meth:`emsm.core.argparse_.ArgumentParser.args`
        """
        # Get the name of the selected plugin.
        args = self._app.argparser().args()
        plugin_name = args.plugin

        # Break if no plugin has been selected.
        if plugin_name is None:
            log.info("no plugin for run selected.")
            return None

        # Execute the plugin.
        log.info("running plugin '{}' ...".format(plugin_name))
        plugin = self._plugins[plugin_name]
        plugin.run(args)
        return None

    def finish(self):
        """
        Calls :meth:`~emsm.core.base_plugin.BasePlugin.finish` for each loaded
        plugin.
        """
        log.info("finish plugins ...")

        finish_queue = self._plugins.values()
        finish_queue = sorted(finish_queue, key=lambda p: p.FINISH_PRIORITY)

        for plugin in finish_queue:
            plugin.finish()
        return None
