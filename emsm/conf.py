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
    "Configuration"
    ]


# Classes
# ------------------------------------------------

class ConfigParser(configparser.ConfigParser):
    """
    Extends the standard Python configparser.ConfigParser by some
    useful methods.
    """

    # Written at the begin of the configuration file.
    EPILOG = tuple()

    def __init__(self, path):
        """
        Parameters:
            * path
                The path to the configuration file.
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
        OVERWRITES

        Reads the configuration from ``path()``.

        See also:
            * path()
        """
        try:
            with open(self._path, "r") as file:
                super().read_file(file)
        except (FileNotFoundError, IOError):
            pass
        return None

    def write(self):
        """
        OVERWRITES

        Writes the configuration into the file at ``path()``.

        See also:
            * path()
        """
        # Get the comment prefix.
        comment_prefix = self._comment_prefixes[0]
        comment_format = "{} {{}}".format(comment_prefix)
        
        # Convert the EPILOG to comment lines.
        epilog = map(lambda s: comment_format.format(s),
                     type(self).EPILOG.split("\n"))
        epilog = "\n".join(epilog) + "\n\n"

        # Write the configuration into the file.
        with open(self._path, "w") as file:
            file.write(epilog)
            super().write(file)
        return None


class MainConfiguration(ConfigParser):
    """
    Handles the *main.conf* configuration file.

    This file includes the configuration for the EMSM Application and the
    plugins.

    The EMSM uses the section '[emsm]' and each plugin has its own section
    with the plugin name.
    """

    EPILOG = (
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
        See also:
            * ConfigParser
        """
        super().__init__(path)

        # Add the default configuration for the EMSM.
        self.add_section("emsm")
        self["emsm"]["user"] = "minecraft"
        self["emsm"]["timeout"] = "0"
        return None
    

class ServerConfiguration(ConfigParser):
    """
    Handles the *server.conf* configuration file, which defines the
    names and resources (url, executable filename, ...) for the EMSM
    known servers.

    See also:
        * ServerWrapper.conf()
    """

    EPILOG = (
        "TRY TO USER *http* IF *https* DOES NOT WORK.\n"
        "\n"
        "[vanilla_latest]\n"
        "server = minecraft_server.jar\n"
        "url = http://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar\n"
        "start_cmd = java -jar {server} nogui.\n"
        "\n"
        "[bukkit_latest]\n"
        "server = craftbukkit.jar\n"
        "url = http://dl.bukkit.org/latest-rb/craftbukkit.jar\n"
        "start_cmd = java -jar {server}\n"
        )
    

class WorldsConfiguration(ConfigParser):
    """
    Handles the *worlds.conf* configuration file, which defines the
    names and settings of all worlds managed by the EMSM.

    See also:
        * WorldWrapper.conf()
    """

    EPILOG = (
        "[the world's name]\n"
        "port = <auto> | int\n"
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
        Like ConfigParser, but populates the 'DEFAULT' section.

        See also:
            * ConfigParser
        """
        super().__init__(path)

        # Populate the defaults section.
        defaults = self.defaults()
        defaults["port"] = "<auto>"
        defaults["stop_timeout"] = "10"
        defaults["stop_delay"] = "5"
        defaults["stop_message"] = "The server is going down.\n"\
                                   "Hope to see you soon."
        return None
    

class Configuration(object):
    """
    Manages all configuration files of a EMSM application
    object.
    """

    def __init__(self, app):
        """
        """
        self._app = app
        self._dir = app.paths().conf_dir()

        self._main = MainConfiguration(os.path.join(self._dir, "main.conf"))
        self._server= ServerConfiguration(os.path.join(self._dir, "server.conf"))
        self._worlds = WorldsConfiguration(os.path.join(self._dir, "worlds.conf"))
        return None

    def main(self):
        """
        The wrapper for the *main.conf* configuration file.

        See also:
            * MainConfiguration
        """
        return self._main

    def server(self):
        """
        The wrapper for the *server.conf* configuration file.

        See also:
            * ServerConfiguration
        """
        return self._server

    def worlds(self):
        """
        The wrapper for the *worlds.conf* configuration file.

        See also:
            * WorldsConfiguration
        """
        return self._worlds

    def read(self):
        """
        Reads all configration files.

        See also:
            * ConfigParser.read()
        """
        # Don't change the order!
        self._main.read()
        self._server.read()
        self._worlds.read()
        return None

    def write(self):
        """
        Writes all configuration files.

        See also:
            * ConfigParser.write()
        """
        self._main.write()
        self._server.write()
        self._worlds.write()
        return None
