#!/usr/bin/env python


# Modules
# ------------------------------------------------
import threading
import urllib.parse
import os

# local (from the application)
import world_wrapper
import server_wrapper
from base_plugin import BasePlugin

# local
from _common_lib import downloadreporthook, userinput


# Data
# ------------------------------------------------
PLUGIN = "Server"

    
# Classes
# ------------------------------------------------
class MyServer(object):
    """
    Wraps an application server wrapper. :)
    """

    def __init__(self, application, server):
        self.application = application
        self.server = server
        return None

    def print_configuration(self):
        """
        Prints the configuration of the server.
        """
        print("{} - configuration:".format(self.server.name))

        configuration = self.server.conf
        for option in configuration:
            print("\t", option, "=", configuration[option])
        return None

    def update(self, force_stop=True, stop_message=str()):
        """
        Updates the server.

        Before the server will be updated, all worlds that are currently
        online with this server, will be stopped.
        """
        print("{} - update: ...".format(self.server.name))
        
        # Get all worlds, that are currently running the server.
        world_filter = lambda w: w.server_wrapper is self.server \
                       and w.is_online()
        world_manager = self.application.world_manager
        worlds = world_manager.get_filtered_worlds(world_filter)

        # Stop those worlds.
        try:
            for world in worlds:
                print("{} - update: Stopping the world '{}' ..."\
                      .format(self.server.name, world.name))
                world.send_command("say {}".format(stop_message))
                world.stop(force_stop)                
        # Do not continue if a world could not be stopped.
        except world_wrapper.WorldStopFailed as error:
            print("{} - update: failure: The world '{}' could not be stopped."\
                  .format(self.server.name, error.world.name))            
        # Continue with the server update if all worlds are offline.
        else:
            reporthook = downloadreporthook.Reporthook(
                url = self.server.url,
                to_file = self.server.server
                )
            print("{} - update: Downloading the server ..."\
                  .format(self.server.name))
            try:
                self.server.update(reporthook)
            except server_wrapper.ServerUpdateFailure as error:
                print("{} - update: failure: {}"\
                      .format(self.server.name, error))
            else:
                print("{} - update: Download is complete."\
                      .format(self.server.name))
        # Restart the worlds.
        finally:
            for world in worlds:
                try:
                    world.start()
                except world_wrapper.WorldIsOnlineError:
                    pass
                except world_wrapper.WorldStartFailed:
                    print("{} - update: failure: The world '{} could not be "\
                          "restarted.".format(self.server.name, world.name))
                else:
                    print("{} - update: The world '{}' has been restated."\
                          .format(self.server.name, world.name))
        return None

    def uninstall(self):
        """
        Uninstalls the server.

        Before the server will be uninstalled, there will be some
        checks to make sure the  server can be uninstalled without
        any side effects.
        """
        server_manager = self.application.server_manager
        
        # We need a server that could replace this one.
        available_server = server_manager.get_available_server()  
        available_server.pop( available_server.index(self.server.name) )

        # Break if there is no other server available.
        if not available_server:
            print("{} - uninstall: failure: There's no other server that "\
                  "replace this one.".format(self.server.name))
            return None
        
        # Make sure, that the server should be removed.
        question = "{} - uninstall: Are you sure, that you want to "\
                   "uninstall the server? ".format(self.server.name)
        if not userinput.ask(question):
            return None
        
        # Get the name of the server that should replace this one.
        prompt = "{} - uninstall: Which server should replace this one?\n\t"\
                 "(Chose from: {}) ".format(self.server.name, available_server)
        check_func = lambda server: server in available_server
        replace_with = userinput.get_value(prompt, check_func=check_func)
        replace_with = server_manager.get_server(replace_with)
        
        # Remove the server.
        try:
            self.server.uninstall(replace_with)
        except server_wrapper.ServerIsOnlineError as error:
            print("{} - uninstall: The server is still running:"\
                  "\n\t'{}'".format(self.server.name, error))
        return None

    
class Server(BasePlugin):
    """
    Public interface for the server wrapper.
    
    """

    version = "1.0.0"
    
    allow_force_stop = False
    update_message = "The server is going down for an update."
    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)

        self.allow_force_stop = self.conf.getboolean(
            "allow_force_stop", self.allow_force_stop)
        self.update_message = self.conf.get(
            "update_message", self.update_message)

        self.conf["allow_force_stop"] = "yes" if self.allow_force_stop else "no"
        self.conf["update_message"] = self.update_message
        return None    

    def setup_argparser_argument_group(self, group):
        group.title = self.name
        group.description = "This plugin provides methods to manage the "\
                            "server files and the server configuration."
        
        # Which server?
        server_manager = self.application.server_manager
        available_server = server_manager.get_available_server()

        group.add_argument(
            "--server",
            action = "append",
            choices = available_server,
            metavar = "SERVER",
            dest = "server",
            default = list(),
            help = "Selects a server."
            )
        group.add_argument(
            "--all-server",
            action = "store_const",
            dest = "all_server",
            default = False,
            const = True,
            help = "Selects all server."
            )        
        
        # Method?
        group.add_argument(
            "--print-configuration",
            action = "count",
            dest = "print_server_conf",
            help = "Prints the configuration section of the server."
            )
        group.add_argument(
            "--update",
            action = "count",
            dest = "update_server",
            help = "Updates the selected server."
            )
        group.add_argument(
            "--uninstall",
            action = "count",
            dest = "uninstall_server",
            help = "Removes the server."
            )
        return None

    def run(self, args):
        # Get the selected server.
        server_manager = self.application.server_manager
        if args.all_server:
            server = server_manager.get_all_server()
        else:
            server = [server_manager.get_server(s) for s in args.server]
            
        # And action:
        for s in server:
            
            s = MyServer(self.application, s)
            
            if args.print_server_conf:
                s.print_configuration()
                
            if args.update_server:
                s.update(self.allow_force_stop, self.update_message)
                
            if args.uninstall_server:
                s.uninstall()
        return None
