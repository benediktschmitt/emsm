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

# emsm
import emsm


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

    The EMSM distinguishes two primary folders:
    The *instance* folder, where the worlds, server, configuration and plugins
    of the user are placed. The *instance* folder can actually be considered to
    be the working directory of the EMSM.
    On the other side is the EMSM installation directory. The *emsm* directory.
    This directory is usually placed in Python's third party library folder
    (site-packages) and contains the EMSM core application and the core plugins.

    #. *emsm* directory:

        .. code-block:: none

            |- emsm
                |- core
                    |- lib
                        |- ...
                    |- __init__.py
                    |- application.py
                    |- argparse_.py
                    |- base_plugin.py
                    |- ...
                |- plugins
                    |- __init__.py
                    |- backups.py
                    |- emsm.py
                    |- guard.py
                    |- ...
                |- __init__.py

    #. *instance* folder:

        .. code-block:: none

            |- instance             # usually /opt/minecraft
                |- conf             # the emsm configuration files
                    |- main.conf
                    |- server.conf
                    |- worlds.conf
                |- plugins          # the user's plugins.
                    |- __init__.py
                    |- myawesomeplugin.py
                    |- ...
                |- plugins_data     # data generated or needed by the plugins
                    |- backups
                    |- emsm
                    |- guard
                    |- ...
                    |- myawesomeplugin
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
                    |- ...
                |- minecraft.py
    """

    def __init__(self, instance_dir):
        """
        """
        self._instance_dir = instance_dir
        self._emsm_dir = os.path.dirname(emsm.__file__)
        return None

    def create(self):
        """
        Creates the folders used by the EMSM Application.

        This method should only be called, after the EMSM downgraded it's
        priviliges.
        """
        def make_dir(path):
            """
            Creates the directory *path* if it does not exist or
            returns silently, if it does.
            """
            try:
                os.makedirs(path, exist_ok=True)
            except OSError:
                pass
            return None

        make_dir(self.instance())
        make_dir(self.conf())
        make_dir(self.plugins())
        make_dir(self.plugins_data())
        make_dir(self.server())
        make_dir(self.worlds())
        make_dir(self.logs())
        return None

    # EMSM

    def emsm(self):
        """
        Returns the path to the *emsm* installation directory. This folder
        is usually located in Python's ``site-packages`` directory.
        """
        return self._emsm_dir

    def emsm_core(self):
        """
        Returns the path to the *emsm.core* directory.
        """
        return os.path.join(self._emsm_dir, "core")

    def emsm_plugins(self):
        """
        Returns the path to the *emsm.plugins* directory. The directory contains
        the core plugins like *worlds*, *server*, *backups*, ...
        """
        return os.path.join(self._emsm_dir, "plugins")

    # Instance

    def instance(self):
        """
        The *instance* folder contains all data generated by the EMSM
        application and the minecraft worlds.
        """
        return self._instance_dir

    def conf(self):
        """
        Contains the configuration files of the EMSM. **Not** the configuration
        for the minecraft worlds. These are still located in the world folder.

        The directory contains the *main.conf*, *server.conf* and
        *worlds.conf* file.

        The directory is located in the *instance* folder.
        """
        return os.path.join(self._instance_dir, "conf")

    def plugins(self):
        """
        Contains all user plugins and plugin packages.

        The directory is located in the *instance* folder.

        .. seealso:: :meth:`emsm_plugins`
        """
        return os.path.join(self._instance_dir, "plugins")

    def plugins_data(self):
        """
        The directory that contains the data generated or used by all plugins.

        The directory is located in the *instance* folder.

        .. seealso:: :meth:`plugin_data``
        """
        return os.path.join(self._instance_dir, "plugins_data")

    def plugin_data(self, plugin_name):
        """
        This directory contains all data of the plugin with the name
        *plugin_name*.

        The directory is a subfolder of :meth:`plugins_data`.
        """
        return os.path.join(self.plugins_data(), plugin_name)

    def server(self):
        """
        This directory contains all server executables specified in
        the ``server.conf`` configuration file.

        The directory is located in the *instance* folder.

        .. seealso:: :meth:`server_`
        """
        return os.path.join(self._instance_dir, "server")

    def server_(self, server_name):
        """
        This directory contains the server software for the server with the
        name *server_name*.

        The directory is located in the :meth:`server` folder.

        .. todo::

            * Try to find better names for *server* and *server_*. They are hard
              to distinguish.
        """
        return os.path.join(self.server(), server_name)

    def worlds(self):
        """
        Contains for each world in ``worlds.conf`` one folder that contains
        the data generated by the minecraft server.

        The directory is located in the *instance* folder.

        .. seealso:: :meth:`world`
        """
        return os.path.join(self._instance_dir, "worlds")

    def world(self, world_name):
        """
        This directory contains the data generated by the minecraft server
        which powers the world *world_name*.
        It contains among others those files:

            * :file:`server.properties`
            * :file:`ops.json`
            * :file:`whitelist.json`

        Furthermore, it is a child of :meth:`worlds`.
        """
        return os.path.join(self.worlds(), world_name)

    def logs(self):
        """
        Contains the EMSM log files.

        Note, that this is NOT the log directory of the minecraft server.
        """
        return os.path.join(self._instance_dir, "log")
