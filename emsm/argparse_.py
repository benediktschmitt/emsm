#!/usr/bin/env python3


# Modules
# ------------------------------------------------
import argparse


# Data
# ------------------------------------------------
__all__ = ["ArgumentParser"]


# Classes
# ------------------------------------------------
class ArgumentParser(object):    
    """
    Wraps the argparse.ArgumentParser that is used
    by the application.
    """
    
    def __init__(self):
        # The help page will be reeanabled before parsing all
        # arguments.
        self._parser = argparse.ArgumentParser(
            description = "Extendable Minecraft Server Wrapper (EMSW)",
            epilog = "Visit benediktschmitt.de for further information.",
            add_help = False)

        self._help_is_enabled = False
        self._args = argparse.Namespace()
        self._plugin_group = self._parser.add_argument_group(title = "Plugin")
        return None 
    
    # get
    # --------------------------------------------

    # The argument group that should contain the arguments
    # used by the invoked plugin.
    plugin_group = property(lambda self: self._plugin_group)

    args = property(lambda self: self._args)

    # arguments
    # --------------------------------------------
    
    def add_application_args(self, available_worlds, available_plugins, version):
        """
        Adds the arguments that are needed by the application
        to the argparser.

        available_worlds is a list with the names of the worlds
        that can be used as an argument.

        available_plugins is a list with the names of the plugins
        that can be invoked.
        """
        self._parser.add_argument(
            "--version",
            action = "version",
            version = "EMSM {}".format(version),
            )
        
        worlds_group = self._parser.add_mutually_exclusive_group()
        worlds_group.add_argument(
            "-w", "--world",
            action = "append",
            dest = "worlds",
            metavar = "WORLD",
            choices = available_worlds,
            default = list(),
            help = "Selects single worlds."
            )
        worlds_group.add_argument(
            "-aw", "--all-worlds",
            action = "store_const",
            dest = "all_worlds",
            const = True,
            default = False,
            help = "Selects all available worlds."
            )

        self._parser.add_argument(
            "-p", "--plugin",
            metavar = "PLUGIN",
            choices = available_plugins,
            dest = "plugin",
            help = "The name of the plugin that will be invoked."
            )
        return None

    def add_help(self):
        """
        Adds the help page to the arguments if not yet done.
        """
        if not self._help_is_enabled:       
            self._parser.add_argument(
                "-h", "--help",
                action = "help",
                default = argparse.SUPPRESS,
                help = "Show this help message and exit."
                )            
            self._help_is_enabled = True
        return None

    # parse
    # --------------------------------------------
    def parse_known_args(self):
        """
        Parses the known arguments and stores them into self.args
        """
        known, unknown = self._parser.parse_known_args()
        self._args = known
        return None    

    def parse_args(self):
        """
        Parses the all arguments and stores them into self.args.
        """
        self.add_help()
        self._args = self._parser.parse_args()
        return None
