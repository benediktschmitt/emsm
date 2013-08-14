#!/usr/bin/env python3


# Modules
# ------------------------------------------------
import os
import sys
import importlib.machinery
import hashlib

# local
from base_plugin import BasePlugin


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
__all__ = ["PluginException", "PluginUnavailableError",
           "PluginImplementationError", "PluginManager",
           ]


# Exceptions
# ------------------------------------------------
class PluginException(Exception):
    """
    Base exception for all exceptions in this module.
    """
    pass


class PluginUnavailableError(PluginException):
    """
    Raised if a plugin can not be found.
    """

    def __init__(self, plugin, msg=str()):
        self.plugin = plugin
        self.msg = msg
        return None

    def __str__(self):
        temp = "The plugin '{}' is not available. {}"\
               .format(self.plugin, self.msg)
        return temp


class PluginImplementationError(PluginException):
    """
    Raised if a plugin is not correct implemented.
    E.g.:
    The plugin does not inherit the BasePlugin or the module
    variable "PLUGIN" does not point to a valid plugin class.
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
    the application version.
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
    Manages and contains all plugins. Works also as dispatcher
    for the plugins.

    Read the documentation at the base_plugin module for further
    information or take a look at the hello_dolly plugin.

    The following methods make use of the application attributes:
        - import_from_default_directory()
        - prepare_run()
        - run()
    """

    def __init__(self, application):
        self._application = application

        # Maps the module name to the plugin class.
        self._plugin_types = dict()

        # Maps the module name to the plugin instance.
        self._plugins = dict()
        return None

    # get
    # --------------------------------------------

    def get_plugin_type(self, plugin):
        return self._plugin_types[plugin]

    def get_plugin(self, plugin):
        return self._plugins[plugin]

    def plugin_is_available(self, plugin):
        return plugin in self._plugin_types

    def get_available_plugins(self):
        return list(self._plugin_types)

    # import
    # --------------------------------------------

    def _plugin_is_outdated(self, plugin):
        """
        Returns true if the plugin is outdated.
        """
        app_version = self._application.version.split(".")
        plugin_version = plugin.version.split(".")

        if len(plugin_version) < 2:
            return True
        elif app_version[0] != plugin_version[0]:
            return True
        elif app_version[1] != plugin_version[1]:
            return True
        else:
            return False

    def import_plugin(self, path, ignore_outdated=True):
        """
        Imports the plugin from the path.

        if not ignore_outdated, an PluginOutdatedError is raised
        if a plugin is outdated.
        """
        # The module name is the name of the plugin.
        name = os.path.basename(path)
        name = name[:-3]

        # Needed to prevent ImportErrors with the local
        # libraries of the plugin.
        if os.path.dirname(path) not in sys.path:
            sys.path.insert(1, os.path.dirname(path))

        try:
            module = _import_module(name, path)
        except ImportError as error:
            raise PluginUnavailableError(name, error)

        # Check if the module contains a plugin.
        if not hasattr(module, "PLUGIN"):
            msg = "Missing the global var: 'PLUGIN'."
            raise PluginImplementationError(name, msg)

        if not hasattr(module, module.PLUGIN):
            msg = "The module does not contain the class '{}'."\
                  .format(module.PLUGIN)
            raise PluginImplementationError(name, msg)

        plugin = getattr(module, module.PLUGIN)

        # The plugin has to be a subclass of BasePlugin.
        if not issubclass(plugin, BasePlugin):
            msg = "The plugin '{}' is not a subclass of BasePlugin."\
                  .format(module.PLUGIN)
            raise PluginImplementationError(name, msg)

        # And has to be compatible with the current emsm version.
        if self._plugin_is_outdated(plugin):
            if ignore_outdated:
                return None
            else:
                raise PluginOutdatedError(name)

        self._plugin_types[name] = plugin
        return None

    def import_from_directory(self, directory):
        """
        Imports all plugins in the directory.

        Every file that does not start with underscore
        and ends with .py will be treated as plugin file.
        """
        def file_is_plugin(path):
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

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if not file_is_plugin(path):
                continue
            self.import_plugin(path)
        return None

    def import_from_app_plugin_dir(self):
        """
        Imports the plugins from the application's default
        plugins directory.
        """
        directory = self._application.pathsystem.plugins_source_dir
        self.import_from_directory(directory)
        return None

    # init
    # --------------------------------------------

    def init_plugins(self):
        """
        Initialises the plugins by passing a reference of the
        application and the name of the plugin in the application
        trough the constructor.

        When this method is called a second time, only the plugins
        that have not been initialised yet, will be initialised.
        """
        init_queue = self._plugin_types.items()
        init_queue = sorted(init_queue, key=lambda e: e[1].init_priority)
        
        for name, plugin_type in init_queue:
            if name in self._plugins:
                continue
            plugin_obj = plugin_type(self._application, name)
            self._plugins[name] = plugin_obj
        return None

    # run
    # --------------------------------------------

    def prepare_run(self):
        """
        Sets the argparser plugin group up.
        """
        arg_parser = self._application.argparser
        arg_group = arg_parser.plugin_group
        invoked_plugin = arg_parser.args.plugin

        if invoked_plugin is not None:
            plugin = self._plugins[invoked_plugin]
            plugin.setup_argparser_argument_group(arg_group)
        return None


    def run(self):
        """
        Calls the run method of the invoked plugin.
        """
        arg_parser = self._application.argparser
        args = arg_parser.args
        invoked_plugin = arg_parser.args.plugin

        if invoked_plugin is not None:
            plugin = self._plugins[invoked_plugin]
            plugin.run(args)
        return None

    # finish
    # --------------------------------------------
    
    def finish(self):
        """
        Calls the finish method for each plugin.
        """
        finish_queue = self._plugins.values()
        finish_queue = sorted(finish_queue, key=lambda p: p.finish_priority)        
        for plugin in finish_queue:
            plugin.finish()
        return None
