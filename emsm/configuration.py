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
The configuration classes validates the values in the configuration
files so that they can be used in the application without raising
ValueError or TypError.
"""


# Modules
# ------------------------------------------------
import os
import urllib.parse
import configparser
import collections

# local
import app_lib.network


# Backward compatibility
# ------------------------------------------------
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError


# Data
# ------------------------------------------------
__all__ = ["ConfigurationError", "MissingOptionError",
           "ValueError_", "Configuration",
           ]


# Exceptions
# ------------------------------------------------
class ConfigurationError(Exception):
    """ Base class for all exceptions in this module. """
    pass


class MissingOptionError(ConfigurationError, KeyError,
                              configparser.NoOptionError):
    """
    Raised if a required option is not defined in a section.
    """

    def __init__(self, option, section, conf_file):
        self.option = option
        self.section = section
        self.conf_file = conf_file
        return None

    def __str__(self):
        temp = "The option '{}' is not defined in the "\
               "section '{}' in the confuration '{}'."\
               .format(self.option, self.section, self.conf_file)
        return temp


class OptionValueError(ConfigurationError, ValueError):
    """
    Raised if the value of an option is not valid.
    """

    def __init__(self, option, section, conf_file, msg=""):
        self.option = option
        self.section = section
        self.conf_file = conf_file
        self.msg = msg
        return None

    def __str__(self):
        temp = "The value for the option '{}' in the section '{}' "\
               "in the configuration '{}' is invalid. {}"\
               .format(self.option, self.section, self.conf_file, self.msg)
        return temp


# Classes
# ------------------------------------------------
class BaseConfigurationFile(object):
    """
    The base class for all configuration files.
    Wraps a configparser.ConfigParser.
    """

    # List of strings that should be written as comments
    # before the configuration.
    epilog = list()

    # Default values
    defaults = None

    def __init__(self, file):
        """
        file is the path to the configuration file.
        """
        self.file = file
        self.conf = self._get_parser()
        return None

    def _get_parser(self):
        """
        Returns a configparser.ConfigParser.
        """                
        parser = configparser.ConfigParser(
            defaults=self.defaults,
            allow_no_value=False,
            strict=True,
            empty_lines_in_values=False,
            interpolation=configparser.ExtendedInterpolation()
            )
        return parser

    # validation
    # --------------------------------------------

    def _validate_section(self, section_name, section):
        """
        Should raise an error if the section contains invalid
        options or values.

        This method can be overwritten.
        """
        return None

    def _validate(self):
        """
        Validates the whole configuration.

        Calls self._validate_section(...) for each section in
        the configuration.

        Can be overwritten.
        """
        for section_name in self.conf:
            section = self.conf[section_name]
            self._validate_section(section_name, section)
        return None

    # completion
    # --------------------------------------------

    def _complete_section(self, section_name, section):
        """
        Should check the values in the section and complete
        them if neccessairy.

        This method can be overwritten.
        """
        return None

    def _complete(self):
        """
        Calls _complete_section for each section in the configuratioin.
        """
        for section_name in self.conf:
            section = self.conf[section_name]
            self._complete_section(section_name, section)
        return None

    # read / write
    # --------------------------------------------

    def read(self):
        try:
            with open(self.file) as file:
                self.conf.read_file(file)
        # XXX: Remove IOError when backward compatibility
        # is not needed anymore.
        except (FileNotFoundError, IOError):
            with open(self.file, "w") as file:
                pass

        self._complete()
        self._validate()
        return None

    def write(self):
        self._complete()
        self._validate()

        # Write the epilog into the file.
        comment_prefix = self.conf._comment_prefixes[0]
        comment_format = "{} {{}}".format(comment_prefix)

        epilog = [comment_format.format(line) for line in self.epilog]
        epilog = "\n".join(epilog) + "\n\n"

        with open(self.file, "w") as file:
            file.write(epilog)
            self.conf.write(file)
        return None


class MainConfiguration(BaseConfigurationFile):
    """
    Handles the main.conf configuration file.

    This configuration includes the parameters for the core application
    and the plugins.
    """

    epilog = (
        "This file contains the settings for the core application and the",
        "plugins.",
        "The section of the core application is:",
        "",
        "[emsm]",
        "user = minecraft",
        "loglevel = WARNING",
        "logfile = emsm.log",
        "timeout = -1",
        "",
        "The configuration section of each plugin is titled with the plugins ",
        "name."
        )

    def _get_parser(self):
        # We use the default parser configuration and add the
        # default values for the core application.
        parser = BaseConfigurationFile._get_parser(self)

        parser.add_section("emsm")
        parser["emsm"]["user"] = "minecraft"
        parser["emsm"]["loglevel"] = "WARNING"
        parser["emsm"]["logfile"] = "emsm.log"
        parser["emsm"]["timeout"] = "-1"
        return parser

    def _validate_section(self, section_name, section):
        if section_name != "emsm":
            return None

        # Log
        section["loglevel"] = section["loglevel"].upper()
        if section["loglevel"] not in ("NOTSET", "DEBUG", "INFO", "WARNING",
                                       "ERROR", "CRITICAL"):
            raise OptionValueError("loglevel", section_name, self.file)

        # The timeout for the LockFile has to be -1 (for infinity)
        # or a number >= 0.
        if section["timeout"] != "-1" and not section["timeout"].isdigit():
            raise OptionValueError("timeout", section_name, self.file)
        return None


class ServerConfiguration(BaseConfigurationFile):
    """
    Handles the server.conf configuration file, which includes
    the names and parameters for all minecraft server that can
    be used with this application.
    """

    epilog = (
        "Try to use *http* if *https* does not work.",
        "",
        "[vanilla_latest]",
        "server = minecraft_server.jar",
        "start_args = nogui.",
        "url = http://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar",
        "java_args = -jar",
        "",
        "[bukkit_latest]",
        "server = craftbukkit.jar",
        "start_args = ",
        "url = http://dl.bukkit.org/latest-rb/craftbukkit.jar",
        "java_args = -jar"
        )

    def _complete_section(self, section_name, section):
        if section_name == self.conf.default_section:
            return None

        # Use the name of the section as filename for the executable,
        # if the server option is not set.
        if not "server" in section or section["server"].isspace():
            section["server"] = section_name.replace(" ", "_")

        # Make sure, that all optional parameters are initialized.
        if not "java_args" in section:
            section["java_args"] = ""
        return None

    def _validate_section(self, section_name, section):
        # Ignore the default section.
        if section_name == self.conf.default_section:
            return None

        # the server executable
        if not "server" in section:
            raise MissingOptionError("server", section_name, self.file)

        # download url of the server
        if not "url" in section:
            raise MissingOptionError("url", section_name, self.file)
        else:
            try:
                urllib.parse.urlparse(section["url"])
            except urllib.error:
                raise OptionValueError("url", section_name, self.file)
        return None


class WorldsConfiguration(BaseConfigurationFile):
    """
    Handles the worlds.conf configuration file, which includes
    the worlds that are manage by this application and the parameters
    of those worlds.
    """

    epilog = (
        "[the world's name]",
        "port = <auto> | int",
        "stop_timeout = int",
        "stop_message = string",
        "stop_delay = int",
        "server = a server in server.conf",
        "",
        "Note, that some plugins may offer you some more options for",
        "a world, like *autostart*. Take a look at the plugins help page",
        "or documentation for further information.",
        )
    
    defaults = collections.OrderedDict(
        port="<auto>",
        stop_timeout="10",
        stop_message="The server is going down.\n\tHope to see you soon.",
        stop_delay="5",
        )

    # An error will be raised if a world configuration uses
    # a server that is not in this list.
    known_server = list()

    def _validate_section(self, section_name, section):
        # server
        if "server" not in section:
            if section_name != self.conf.default_section:
                raise MissingOptionError("server", section_name, self.file)
        elif section["server"] not in self.known_server:
            msg = "The server '{}' has not been found in *server.conf*."\
                  .format(section["server"])
            raise OptionValueError("server", section_name, self.file, msg)

        # port
        if section_name == self.conf.default_section \
           and section["port"] == "<auto>":
            pass
        elif not (section["port"].isdigit() \
                and 0 < section.getint("port") < 65535):
            msg = "Has to be '<auto>' or an integer value between 0 and 65535."
            raise OptionValueError("port", section_name, self.file, msg)

        # stop
        if not section["stop_delay"].isdigit():
            msg = "Has to be an integer value."
            raise OptionValueError("stop_delay", section_name, self.file)

        if not section["stop_timeout"].isdigit():
            msg = "Has to be an integer value."
            raise OptionValueError("stop_timeout", section_name, self.file)
        return None

    def _complete_section(self, section_name, section):
        if section_name == self.conf.default_section:
            return None
        
        # Find an unused port.
        if section["port"] == "<auto>":
            unused_port = app_lib.network.get_unused_port(10000, 30000)
            section["port"] = str(unused_port)
        return section


class Configuration(object):
    """
    Loads an manages all configuration files of the application.
    """

    def __init__(self, app):
        """
        main_conf_dir is the directory that contains all configuration files.
        """
        self._app = app
        self._dir = app.paths.conf_dir
        
        self._main = MainConfiguration(
            os.path.join(self._dir, "main.conf"))
        self._server= ServerConfiguration(
            os.path.join(self._dir, "server.conf"))
        self._worlds = WorldsConfiguration(
            os.path.join(self._dir, "worlds.conf"))
        return None

    # get
    # --------------------------------------------

    # No one needs access to the underlaying wrapper.

    main = property(lambda self: self._main.conf)
    server = property(lambda self: self._server.conf)
    worlds = property(lambda self: self._worlds.conf)

    # common read / write
    # --------------------------------------------

    def read(self):
        """
        Reads all configuration files.
        """
        self._main.read()
        self._server.read()
        # Tell the worlds configuration which server are known.
        self._worlds.known_server = self._server.conf.sections()
        self._worlds.read()
        return None


    def write(self):
        """
        Writes all configuration files.
        """
        self._main.write()
        self._server.write()
        # Tell the worlds configuration which server are known.
        self._worlds.known_server = self._server.conf.sections()
        self._worlds.write()
        return None
