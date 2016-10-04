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
import logging
import shutil
import warnings

# third party
import blinker

# emsm
from . import argparse_
from .lib import userinput
from .worlds import WorldWrapper


# Data
# ------------------------------------------------

__all__ = [
    "BasePlugin"
    ]

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class BasePlugin(object):
    """
    This is the base class for all plugins.


    If you want to know, how to implement your own plugin, you should also
    take a look at the :mod:`plugins.hellodolly` plugin.
    """

    #: Integer with the init priority of the plugin.
    #: A higher value results in a later initialisation.
    INIT_PRIORITY = 0

    #: Integer with the finish priority of the plugin.
    #: A higher value results in a later call of the finish method.
    FINISH_PRIORITY = 0

    #: The last version number of the EMSM version that worked correctly
    #: with that plugin.
    VERSION = "0.0.0"

    #: The plugin package can be downloaded from this url.
    #:
    #: .. seealso::
    #:
    #:      * :mod:`emsm.plugins.plugins` package manager
    DOWNLOAD_URL = str()

    #: This string is displayed when the ``--long-help`` argument is used.
    DESCRIPTION = str()

    #: If ``True``, the plugin has no :meth:`argparser` and can therefore
    #: not be invoked from the command line.
    HIDDEN = False

    #: Signal, that is emitted, when a plugin has been uninstalled.
    plugin_uninstalled = blinker.signal("plugin_uninstalled")

    def __init__(self, app, name):
        """
        Initialises the configuration and the storage of the plugin.

        **Override:**

            * Extend, but do not override.
        """
        log.info("initialising '{}' ...".format(name))

        self.__app = app
        self.__name = name

        # Get the argparser for this plugin and set it up.
        if type(self).HIDDEN:
            self.__argparser = None
        else:
            self.__argparser = app.argparser().plugin_parser(name)
            self.__argparser.add_argument(
                "--long-help",
                action = argparse_.LongHelpAction,
                description = type(self).DESCRIPTION
                )
        return None

    def app(self):
        """
        Returns the parent EMSM :class:`~emsm.application.Application`
        that owns this plugin.
        """
        return self.__app

    def name(self):
        """
        Returns the name of the plugin.
        """
        return self.__name

    def conf(self):
        """
        Returns a dictionary like object that contains the configuration
        of the plugin.

        .. deprecated:: 4.0.16-beta

            This method has been replaced by :meth:`global_conf` to clarify
            the difference to :meth:`world_conf`.
        """
        msg = "The BasePlugin.conf() method has been marked as deprecated. "\
            "Please use BasePlugin.global_conf() instead."
        warnings.warn(msg, DeprecationWarning)
        return self.global_conf()

    def global_conf(self):
        """
        Returns a dictionary like object, that contains the *global*
        configuration of the plugin (:file:`plugins.conf`).

        :seealso: :meth:`world_conf`
        """
        # Make sure the configuration section exists.
        main_conf = self.__app.conf().main()
        if not self.__name in main_conf:
            log.info(
                "creating configuration section for '%s' in '%s'.",
                self.__name, main_conf.path()
            )

            main_conf.add_section(self.__name)

            log.info(
                "created configuration section for '%s' in '%s'.",
                self.__name, main_conf.path()
            )
        return main_conf[self.__name]

    def world_conf(self, world):
        """
        Returns a dictionary like object, that contains the *world* specific
        configuration of the plugin (:file:`foo.world.conf`).

        :seealso: :meth:`global_conf`

        :arg world:
            The :class:`WorldWrapper` of the world or the world's name (str).
        """
        # Get the world's name.
        world_name = world.name() if isinstance(world, WorldWrapper) else world

        # Make sure, the configuration section exists.
        conf = self.__app.conf().world(world_name)
        section_name = "plugin:{}".format(self.__name)
        if not section_name in conf:
            log.info(
                "creating configuration section for '%s' in '%s'.",
                self.__name, conf.path()
            )

            conf.add_section(section_name)

            log.info(
                "created configuration section for '%s' in '%s'.",
                self.__name, conf.path()
            )
        return conf[section_name]

    def data_dir(self, create=True):
        """
        Returns the directory that contains all data created by the plugin
        to manage its EMSM job.

        :param bool create:
            If the directory does not exist, it will be created.

        .. seealso::

            * :meth:`emsm.core.paths.Pathsystem.plugin_data_dir`
        """
        data_dir = self.__app.paths().plugin_data(self.__name)

        # Make sure the directory exists.
        if not os.path.exists(data_dir) and create:
            log.info("creating data directory for '{}'.".format(self.__name))

            os.makedirs(data_dir)

            log.info("created data directory for '{}'.".format(self.__name))

        return data_dir

    def argparser(self):
        """
        Returns the :class:`argparse.ArgumentParser` that is used by this
        plugin.

        If :attr:`HIDDEN` is ``True``, *None* is returned, since the plugin
        has no argument parser.

        .. seealso::

            * :meth:`emsm.core.argparse_.ArgumentParser.plugin_parser`
        """
        return self.__argparser

    def _uninstall(self):
        """
        This method is called by *uninstall()* and should remove all
        data or configuration generated by the plugin.

        **Subclass:**

            * You may completly override this method.
        """
        return None

    def uninstall(self):
        """
        Called when the plugin should be uninstalled. This method
        is interactive and requires the user to confirm if and which
        data should be removed.

        The BasePlugin removes:

            * the plugin module (the *.py* file in *plugins*)
            * the plugin data directory
            * the plugin configuration

        **Subclass:**

            Subclasses should override the :meth:`_uninstall` method.

        **Signals:**

            * :attr:`plugin_uninstalled`

        .. seealso::

            * :meth:`data_dir`
            * :meth:`conf`
            * :meth:`_uninstall`
        """
        log.info("uninstalling '{}' ...".format(self.__name))

        # Make sure the user really wants to uninstall the plugin.
        if not userinput.ask("Do you really want to remove '{}'?"\
                             .format(self.__name)
                             ):
            # I did not want to implement a new exception type for this case.
            # I think KeyboardInterrupt is good enough.
            log.info("cancelled uninstallation of '{}'.".format(self.__name))
            return None

        # Remove the python module that contains the plugin.
        plugin_module = self.__app.plugins().get_module(self.__name)
        if plugin_module:
            os.remove(plugin_module.__file__)

            log.info("removed '{}' module at '{}'."\
                     .format(self.__name, plugin_module.__file__)
                     )

        # Remove the plugin data directory.
        if userinput.ask("Do you want to remove the data directory?"):
            shutil.rmtree(self.data_dir(), True)

            log.info("removed '{}' plugin data directory at '{}'."\
                     .format(self.__name, self.data_dir(create=False))
                     )

        # Remove the configuration.
        if userinput.ask("Do you want to remove the configuration?"):
            self.__app.conf().main().remove_section(self.__name)

            log.info("removed '{}' configuration section in '{}'."\
                     .format(self.__name, self.__app.conf().main().path())
                     )

            # Remove the configuration section in every  *.world.conf file.
            for world_conf in self.__app.conf().worlds():
                world_conf.remove_section("plugin:" + self.name())

        # Remove the subclass stuff.
        self._uninstall()

        # Emit the signal.
        BasePlugin.plugin_uninstalled.send(self)
        return None

    def run(self, args):
        """
        The *main* method of the plugin. This method is called if the plugin
        has been invoked by the command line arguments.

        :params argparse.Namespace args:
                is an argparse.Namespace instance that contains the values
                of the parsed command line arguments.

        Subclass:

            * You may override this method.

        .. seealso::

            * :meth:`argparser`
            * :meth:`emsm.core.argparse_.ArgumentParser.args`
            * :meth:`emsm.core.plugins.PluginManager.run`
        """
        return None

    def finish(self):
        """
        Called when the EMSM application is about to finish. This method can
        be used for background jobs or clean up stuff.

        Subclass:

            * You may override this method.

        .. seealso::

            * :meth:`emsm.core.plugins.PluginManager.finish`
        """
        return None
