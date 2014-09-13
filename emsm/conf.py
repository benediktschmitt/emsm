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
import configparser


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
    "WorldsConfiguration",
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

    #: Written at the begin of the configuration file.
    _EPILOG = str()

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
        comment_format = "{} {{}}".format(comment_prefix)
        
        # Convert the EPILOG to comment lines.
        epilog = map(lambda s: comment_format.format(s),
                     type(self)._EPILOG.split("\n"))
        epilog = "\n".join(epilog) + "\n\n"

        # Write the configuration into the file.
        with open(self._path, "w") as file:
            file.write(epilog)
            super().write(file)
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

        [backups]
        include_server = ...
        # ...
    """

    _EPILOG = (
        "This file contains the settings for the EMSM core application and\n"
        "the plugins.\n"
        "\n"
        "The section of the EMSM looks like this per default:\n"
        "\n"
        "[emsm]\n"
        "user = minecraft\n"
        "loglevel = WARNING\n"
        "timeout = -1\n"
        "\n"
        "The configuration section of each plugin is titled with the plugins\n"
        "name."
        )

    def __init__(self, path):
        """
        """
        super().__init__(path)

        # Add the default configuration for the EMSM.
        self.add_section("emsm")
        self["emsm"]["user"] = "minecraft"
        self["emsm"]["timeout"] = "0"
        return None

    
class WorldsConfiguration(ConfigParser):
    """
    Handles the *worlds.conf* configuration file, which defines the
    names and settings of all worlds managed by the EMSM.

    .. seealso::
    
        * :meth:`emsm.worlds.WorldWrapper.conf`
    """

    _EPILOG = (
        "[the world's name]\n"
        "stop_timeout = int\n"
        "stop_message = string\n"
        "stop_delay = int\n"
        "server = a server in server.conf\n"
        "\n"
        "Note, that some plugins may offer you some more options for\n"
        "a world, like *enable_initd*. Take a look at the plugins help page\n"
        "or documentation for further information.\n"
        )

    def __init__(self, path):
        """
        """
        super().__init__(path)

        # Populate the defaults section.
        defaults = self.defaults()
        defaults["stop_timeout"] = "10"
        defaults["stop_delay"] = "5"
        defaults["stop_message"] = "The server is going down.\n"\
                                   "Hope to see you soon."
        return None
    

class Configuration(object):
    """
    Manages all configuration files of an EMSM application
    object.

    .. seealso::

        * :meth:`emsm.application.Application.conf`
        * :meth:`emsm.paths.Pathsystem.conf_dir`
    """

    def __init__(self, app):
        """
        """
        self._app = app
        self._dir = app.paths().conf_dir()

        self._main = MainConfiguration(os.path.join(self._dir, "main.conf"))
        self._worlds = WorldsConfiguration(os.path.join(self._dir, "worlds.conf"))
        return None

    def main(self):
        """
        Returns the :class:`MainConfiguration`.
        """
        return self._main

    def worlds(self):
        """
        Returns the :class:`WorldsConfiguration`.
        """
        return self._worlds

    def read(self):
        """
        Reads all configration files.
        """
        log.info("reading configuration ...")
        
        # Don't change the order!
        self._main.read()
        self._worlds.read()
        return None

    def write(self):
        """
        Saves all configuration values.
        """
        log.info("writing configuration ...")
        
        self._main.write()
        self._worlds.write()
        return None
