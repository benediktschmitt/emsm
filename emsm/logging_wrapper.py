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
