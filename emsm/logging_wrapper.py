#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


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
