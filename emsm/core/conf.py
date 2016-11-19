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
import configparser

# local
from .worlds import WorldWrapper


# Backward compatibility
# ------------------------------------------------

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError


# Data
# ------------------------------------------------

__all__ = [
    "ConfigParser",
    "MainConfiguration",
    "ServerConfiguration",
    "WorldConfiguration",
    "Configuration"
    ]

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class ConfigParser(configparser.ConfigParser):
    """
    Extends the standard Python :class:`configparser.ConfigParser` by some
    useful methods.

    :param str path:
        The path to the configuration file. This file is used, when you call
        :meth:`read` or :meth:`write`.
    """

    def __init__(self, path):
        """
        """
        super().__init__(
            allow_no_value = False,
            strict = True,
            empty_lines_in_values = False,
            interpolation=configparser.ExtendedInterpolation()
            )
        self._path = path
        return None

    def epilog(self):
        """
        Returns a comment, which is written at the begin of a configuration
        file.
        """
        return ""

    def path(self):
        """
        Returns the path of the configuration file.
        """
        return self._path

    def read(self):
        """
        Reads the configuration from :meth:`path`.
        """
        try:
            with open(self._path, "r") as file:
                super().read_file(file)
        except (FileNotFoundError, IOError):
            pass
        return None

    def write(self):
        """
        Writes the configuration into :meth:`path`.
        """
        # Get the comment prefix.
        comment_prefix = self._comment_prefixes[0]

        # Convert the EPILOG to comment lines.
        epilog = self.epilog().split("\n")
        epilog = [comment_prefix + " " + line for line in epilog]
        epilog = "\n".join(epilog) + "\n\n"

        # Write the configuration into the file.
        with open(self._path, "w") as file:
            file.write(epilog)
            super().write(file)
        return None

    def remove(self):
        """
        Removes the configuration file from the file system.
        """
        try:
            os.remove(self.path())
        except FileNotFoundError:
            log.error(
                "could not remove the '%s' configuration file.", self.path()
            )
        return None


class MainConfiguration(ConfigParser):
    """
    Handles the :file:`main.conf` configuration file.

    This file includes the configuration for the EMSM Application and the
    plugins.

    The EMSM owns the ``[emsm]`` section and each plugin has its own section
    with the plugin name.

    .. code-block:: ini

        [emsm]
        user = minecraft
        timeout = 0
        screenrc =

        [backups]
        include_server = ...
        # ...
    """

    def __init__(self, path):
        """
        """
        super().__init__(path)

        # Add the default configuration for the EMSM.
        self.add_section("emsm")
        self["emsm"]["user"] = "minecraft"
        self["emsm"]["timeout"] = "0"
        self["emsm"]["screenrc"] = ""
        return None

    def epilog(self):
        epilog = "\n".join([
            "This file contains the settings for the EMSM core application and",
            "the plugins.",
            "",
            "The section of the EMSM looks like this per default:",
            "",
            "[emsm]",
            "user = minecraft",
            "timeout = -1",
            "screenrc = ",
            "",
            "The configuration section of each plugin is titled with the plugins",
            "name.",
        ])
        return epilog


class ServerConfiguration(ConfigParser):
    """
    Handles the *server.conf* configuration file, which allows the user
    to overwrite the default EMSM settings for a server wrapper like
    the *url* or the *start command*.

    .. seealso::

        * :meth:`emsm.core.server.BaseServerWrapper.conf`
        * :meth:`emsm.core.conf.WorldConfiguration`
    """

    def epilog(self):
        epilog = "\n".join([
            "[server name]",
            "url = string",
            "start_command = string",
            "",
            "The EMSM comes with tested default settings for each server.",
            "so you should only overwrite these values, if you have to.",
        ])
        return epilog


class WorldConfiguration(ConfigParser):
    """
    Handles a configuration file for *one* world and allows the user
    to set custom configuration values for each plugin, server and
    the EMSM.

    :arg str path:
    """

    def __init__(self, path):
        """
        """
        super().__init__(path)

        # Add the default options for the world.
        self.add_section("world")
        self["world"]["stop_timeout"] = "10"
        self["world"]["stop_delay"] = "5"
        self["world"]["stop_message"] = "The server is going down.\n"\
                                        "Hope to see you soon."
        self["world"]["server"] = "vanilla 1.11"
        return None

    def epilog(self):
        filename = os.path.basename(self.path())
        world_name = filename[:-len(".world.conf")]

        epilog = "\n".join([
            "This configuration file contains the configuration for the world",
            "",
            "    **{world_name}**",
            "",
            "This file can be used to override global configuration values in ",
            "the *server.conf* and *main.conf* configuration files.",
            "",
            "[world]",
            "stop_timeout = int",
            "stop_message = string",
            "stop_delay = int",
            "server = a server in server.conf",
            "",
            "Custom options for the backups plugin:",
            "",
            "[plugin:backups]",
            "archive_format = bztar",
            "max_storage_size = 30",
            "",
            "Custom options for the vanilla 1.8 server:",
            "",
            "[server:vanilla 1.8]",
            "start_command = java -Xms512m -Xmx1G -jar {{server_exe}} nogui",
            ""
        ]).format(world_name=world_name)
        return epilog


class Configuration(object):
    """
    Manages all configuration files of an EMSM application
    object.

    .. seealso::

        * :meth:`emsm.core.application.Application.conf`
        * :meth:`emsm.core.paths.Pathsystem.conf_dir`
    """

    def __init__(self, app):
        """
        """
        self._app = app
        self._dir = app.paths().conf()

        self._main = MainConfiguration(os.path.join(self._dir, "main.conf"))
        self._server = ServerConfiguration(os.path.join(self._dir, "server.conf"))

        # Load all *.world.conf configuration files
        # We ignore files, that start with an underscore.
        self._worlds = dict()
        if os.path.exists(self._dir):
            for name in os.listdir(self._dir):
                path = os.path.join(self._dir, name)
                if not os.path.isfile(path):
                    continue
                if not name.endswith(".world.conf"):
                    continue
                if name.startswith("_"):
                    continue

                world_name = name[:-len(".world.conf")]
                self._worlds[world_name] = WorldConfiguration(path)

        WorldWrapper.world_uninstalled.connect(self.__remove_world)
        return None

    def __remove_world(self, world):
        """
        Removes the :class:`WorldConfiguration` of *world* from the internal
        map.
        """
        if world.name() in self._worlds:
            del self._worlds[world.name()]
        return None

    def main(self):
        """
        Returns the :class:`MainConfiguration`.
        """
        return self._main

    def server(self):
        """
        Returns the :class:`ServerConfiguration`.
        """
        return self._server

    def worlds(self):
        """
        Returns a list with all :class:`WorldConfiguration` objects.
        """
        return list(self._worlds.values())

    def world(self, name):
        """
        Returns the :class:`WorldConfiguration` for the world with the name
        *name* and ``None``, if there is not such a world.
        """
        return self._worlds.get(name)

    def list_worlds(self):
        """
        Returns a list with the names of all worlds, for which a configuration
        file has been found.
        """
        return list(self._worlds.keys())

    def read(self):
        """
        Reads all configration files.
        """
        log.info("reading configuration ...")

        # Don't change the order!
        self._main.read()
        self._server.read()
        for conf in self._worlds.values():
            conf.read()
        return None

    def write(self):
        """
        Saves all configuration values.
        """
        log.info("writing configuration ...")

        self._main.write()
        self._server.write()
        for conf in self._worlds.values():
            conf.write()
        return None
