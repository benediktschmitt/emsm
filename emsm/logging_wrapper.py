#!/usr/bin/python3

# Extendable Minecraft Server Manager - EMSM
# Copyright (C) 2013-2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Modules
# ------------------------------------------------
import logging
import os
import sys


# Classes
# ------------------------------------------------
class Logger(object):
    """
    Wrapps the EMSM logger.
    """

    def __init__(self, app):
        """
        """
        self._app = app

        self.root = logging.getLogger()
        self.emsm = logging.getLogger("emsm")
        
        self.fmt = logging.Formatter(
            fmt="{asctime}[{levelname:8}][{name:12}] {message}",
            datefmt="%Y-%m-%d %H:%M:%S", style="{"
            )
        
        self.file = None
        self.file_handler = None
        return None

    def shutdown(self):
        """
        Closes all handler used by the emsm logger.
        """
        self.file_handler.close()
        return None

    def load_conf(self):
        """
        Sets the logger up, using the configuration options.
        """
        def logfile_abspath(logfile):
            """
            Returns the absolute path of the logfile. If the path is relative,
            the emsm root dir is used as root.
            """
            if not os.path.isabs(logfile):
                logfile = os.path.join(self._app.paths.root_dir, logfile)
            logfile = os.path.expanduser(logfile)
            logfile = os.path.abspath(logfile)
            return logfile
        
        # Read the configuration
        conf = self._app.conf.main["emsm"]
        level = conf["loglevel"]
        file = logfile_abspath(conf["logfile"])

        # Apply configuration
        self.root.setLevel(level)

        self.file = file
        self.file_handler = logging.FileHandler(file)
        self.file_handler.setFormatter(self.fmt)
        self.root.addHandler(self.file_handler)
        return None
