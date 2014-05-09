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
import os


# Backward compatibility
# ------------------------------------------------
try:
    FileExistsError
except NameError:
    FileExistsError = OSError


# Data
# ------------------------------------------------
__all__ = ["Pathsystem"]


# Classes
# ------------------------------------------------
class Pathsystem(object):
    """
    Manages the paths to the different files and directories of the
    application.
    """

    # Usually, the root directory of the wrapper is the parent directory of
    # this script.
    DEFAULT_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

    def __init__(self, root_dir=None):
        """
        root_dir is the root directory of the application. If not provided,
        the DEFAULT_ROOT_DIR will be used.
        """
        if root_dir is None:
            root_dir = self.DEFAULT_ROOT_DIR
        root_dir = os.path.expanduser(root_dir)
        root_dir = os.path.abspath(root_dir)
        self._root_dir = root_dir

        # The main subdirectories
        self._dirs = dict()
        self._dirs["conf"] = os.path.join(self._root_dir, "configuration")
        self._dirs["plugins_src"] = os.path.join(self._root_dir, "plugins")
        self._dirs["plugins_data"] = os.path.join(self._root_dir, "plugins_data")
        self._dirs["server"] = os.path.join(self._root_dir, "server")
        self._dirs["worlds"] = os.path.join(self._root_dir, "worlds")
        self._dirs["emsm"] = os.path.join(self._root_dir, "emsm")
        
        # Make sure that the base hierarchy exists.
        self.create()
        return None

    def create(self):
        """
        Creates the basic directory structure used by the application.
        """
        for path in self._dirs.values():
            try:
                os.makedirs(path)
            except FileExistsError:
                pass
        return None

    # paths to the main subdirectories
    # --------------------------------------------

    root_dir = property(lambda self: self._root_dir)

    conf_dir = property(lambda self: self._dirs["conf"])

    server_dir = property(lambda self: self._dirs["server"])

    worlds_dir = property(lambda self: self._dirs["worlds"])

    plugins_src_dir = property(lambda self: self._dirs["plugins_src"])

    plugins_data_dir = property(lambda self: self._dirs["plugins_data"])

    emsm_dir = property(lambda self: self._dirs["emsm"])

    log_filename = property(
        lambda self: os.path.join(self._root_dir, "emsm.log"))

    # paths to topic specific subdirectories
    # --------------------------------------------

    def get_plugin_data_dir(self, plugin):
        """
        Returns the path of the data directory for the plugin.
        There's no guarantee that the directory exists.
        """
        return os.path.join(self.plugins_data_dir, plugin)

    def get_world_dir(self, world):
        """
        Returns the path of the world.
        """
        return os.path.join(self.worlds_dir, world)
