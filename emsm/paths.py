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


# Backward compatibility
# ------------------------------------------------

try:
    FileExistsError
except NameError:
    FileExistsError = OSError


# Data
# ------------------------------------------------

__all__ = [
    "Pathsystem"
    ]


# Classes
# ------------------------------------------------

class Pathsystem(object):
    """
    Manages the paths to the different files and directories of the
    application.

    An EMSM directory tree may look similar to this one:

    .. code-block:: none

        |- EMSM_ROOT
           |- conf             # the emsm configuration files
              |- main.conf
              |- server.conf
              |- worlds.conf
           |- emsm             # the EMSM source files
              |- application.conf
              |- world_wrapper.py
              |- server_wrapper.py
              |- base_plugin.py
              |- ...
           |- plugins          # the plugin's source files
              |- backups.py
              |- guard.py
              |- hellodolly.py
              |- initd.py
              |- server.py
              |- ...
           |- plugins_data     # data generated or needed by the plugins
              |- backups
                 |- foo
                 |- bar
              |- guard
              |- hellodolly.py
                 |- lyrics.txt
              |- initd
              |- ...
           |- server           # the server executables
              |- minecraft_server.jar
              |- craftbukkit.jar
              |- ...
           |- worlds           # the data of the worlds (minecraft map, ...)
              |- foo
                 |- server.properties
                 |- ...
              |- bar
                 |- server.properties
                 |- ...
            |- logs
              |- emsm.log
              |- emsm.log.1
              |- emsm.log.2
              |- ...
    """

    def __init__(self):
        """
        """
        # The root directory is the parent folder of this folder.
        self._root_dir = os.path.dirname(os.path.dirname(__file__))
        self._root_dir = os.path.abspath(self._root_dir)

        self._conf_dir = os.path.join(self._root_dir, "conf")
        self._plugins_dir = os.path.join(self._root_dir, "plugins")
        self._plugins_data_dir = os.path.join(self._root_dir, "plugins_data")
        self._server_dir = os.path.join(self._root_dir, "server")
        self._worlds_dir = os.path.join(self._root_dir, "worlds")
        self._emsm_dir = os.path.join(self._root_dir, "emsm")
        self._log_dir = os.path.join(self._root_dir, "logs")
        return None

    def create(self):
        """
        Creates the folders used by the EMSM Application.
        """
        def make_dir(path):
            """
            Creates the directory *path* if it does not exist or
            breaks silently, if it already exists.
            """
            try:
                os.makedirs(path, exist_ok=True)
            except OSError:
                pass
            return None
                
        make_dir(self._root_dir)
        make_dir(self._conf_dir)
        make_dir(self._plugins_dir)
        make_dir(self._plugins_data_dir)
        make_dir(self._server_dir)
        make_dir(self._worlds_dir)
        make_dir(self._emsm_dir)
        make_dir(self._log_dir)
        return None

    def root_dir(self):
        """
        The root directory contains the *worlds*, *server*, *configuration*,
        *emsm*, .. folders.
        """
        return self._root_dir

    def emsm_root_dir(self):
        """
        Alias for :meth:`root_dir()`.
        """
        return self._root_dir

    def conf_dir(self):
        """
        Contains the configuration files of the EMSM. **Not** the configuration
        for the minecraft worlds. These are still in the world folder.

        This directory contains the *main.conf*, *server.conf* and
        *worlds.conf* file.
        """
        return self._conf_dir

    def plugins_dir(self):
        """
        Contains the source of all plugins that are currently installed.

        This directory usually contains the *world.py*, *server.py* and
        *guard.py* plugins.
        """
        return self._plugins_dir

    def plugins_data_dir(self):
        """
        The directory that contains the data of all plugins.

        .. seealso:: :meth:`plugin_data_dir``
        """
        return self._plugins_data_dir

    def plugin_data_dir(self, plugin_name):
        """
        This directory should contain all data of the plugin with the
        name *plugin_name*.

        Furthermore this directory is a child of :meth:`plugins_data_dir`.
        """
        return os.path.join(self._plugins_data_dir, plugin_name)

    def server_dir(self):
        """
        This directory contains all server executables specified in
        the *server.conf* configuration file.
        """
        return self._server_dir

    def worlds_dir(self):
        """
        Contains for each world in *worlds.conf* one folder that contains
        the data generated by the minecraft server.

        .. seealso:: :meth:`world_dir`
        """
        return self._worlds_dir

    def world_dir(self, world_name):
        """
        This directory contains the data generated by the minecraft server
        like the :file:`server.properties`, :file:`ops.json`,
        :file:`whitelist.json`, ... files.

        Furthermore, it is a child of :meth:`worlds_dir`.
        """
        return os.path.join(self._worlds_dir, world_name)

    def emsm_dir(self):
        """
        Contains the source code of the EMSM application like the
        :file:`server_wrapper.py` and :file:`world_wrapper.py` files.
        """
        return self._emsm_dir

    def log_dir(self):
        """
        Contains the EMSM log files.

        Note, that this is NOT the log directory of the minecraft server.
        """
        return self._log_dir
