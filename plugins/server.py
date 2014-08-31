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
About
-----

This plugin provides a user interface for the server wrapper. It can handle
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

.. code-block:: ini

    [server]
    update_message = The server is going down for an update.

**update_message**
   
    Is a string, printed before stopping a world for an update.

Arguments
---------
   
Select the server with the *common* arguments **--server** or **--all-server**.

.. option:: --configuration
   
    Prints the configuration of the server.

.. option:: --usage

    Prints the names of the worlds, powered by this server.
   
.. option:: --update

    Updates the server. Tries a normal stop of all worlds, that are running this
    server. If the stop fails, the update will be aborted.
   
.. option:: --force-update

    Forces the update of the server by forcing the stop of all worlds, that are
    running the server.
   
.. option:: --uninstall

    Removes the server.
   
    .. hint:: 

        Using this argument is strongly **recommended** if you want to remove a 
        server from the application. Removing a server with this command
        makes sure, that no world is still running the server and that the 
        configuration files keep in a consistent state.
"""


# Modules
# ------------------------------------------------

# std
import os

# local
from emsm import worlds
from emsm import server
from emsm.base_plugin import BasePlugin
from emsm.lib import userinput


# Data
# ------------------------------------------------

PLUGIN = "Server"

    
# Classes
# ------------------------------------------------

class MyServer(object):
    """
    Wraps an EMSM ServerWrapper :).

    Todo:
        * Find a better class name ...
    """

    def __init__(self, app, server):
        self._app = app
        self._server = server
        return None

    def server(self):
        """
        Returns the wrapper ServerWrapper instance.
        """
        return self._server

    def print_status(self):
        """
        Prints a list with the worlds powered by the server.

        See also:
            * WorldWrapper.server()
            * ServerWrapper.is_online()
        """
        # Get all worlds powered by this server.
        worlds = self._app.worlds.get_by_pred(
            lambda w: w.server() is self._server
            )
        online_worlds = list(filter(lambda w: w.is_online(), worlds))
        offline_worlds = list(filter(lambda w: w.is_offline(), worlds))

        # Print the worlds grouped by their current status (offline/online).
        print("{} - usage:".format(self._server.name()))
        if online_worlds:
            print("\t", "online ({}/{}):".format(len(online_worlds), len(worlds)))
            for world in online_worlds:
                print("\t\t", world.name())

        if offline_worlds:
            print("\t", "offline ({}/{}):".format(len(offline_worlds), len(worlds)))
            for world in offline_worlds:
                print("\t\t", world.name())

        if not online_worlds and not offline_worlds:
            print("\t", "- no worlds -")
        return None

    def print_conf(self):
        """
        Prints the configuration of the server.

        See also:
            * ServerWrapper.conf()
        """
        conf = self._server.conf().items()
        
        print("{} - configuration:".format(self._server.name()))
        for key, value in sorted(conf):
            # Make sure, that multiline values have the correct indent.
            value = value.replace("\n", "\n\t\t")
            
            print("\t", key, "=", value)
        return None

    def update(self, force_stop=True, stop_message=str()):
        """
        Updates the server.

        All powered worlds by this server that are currently online, will
        be stopped and restarted after the update.

        Parameters:
            * force_stop
                Force the stop of the worlds by calling
                WorldWrapper.stop(force_stop=True).
            * stop_message
                The message displayed before stopping the server.

        See also:
            * ServerWrapper.update()
            * WorldWrapper.stop()
        """
        print("{} - update: ".format(self._server.name()))
        
        # Get all worlds, powered by this server which are currently
        # online.
        worlds = self._app.worlds().get_by_pred(
            lambda w: w.server() is self._server and w.is_online()
            )

        # Stop those worlds.
        try:
            print("\t", "stopping all running worlds ...")
            for world in worlds:
                print("\t\t", world.name())                
                world.stop(force_stop=force_stop, message=stop_message)
                
        # A world could not be stopped.
        except world_wrapper.WorldStopFailed as err:
            print("\t", "FAILURE: Could not stop the world '{}'."\
                  .format(err.world.name()))
            
        # Continue with the server update if all worlds could be stopped.
        else:
            print("\t", "downloading server executable ...")
            try:
                self._server.update()
            except server.ServerUpdateFailure as err:
                print("\t\t", "FAILURE: Could not download the server "\
                              "executable. (check the url)")
                
        # Restart the worlds.
        finally:
            print("\t", "restarting the worlds ...")
            for world in worlds:
                try:
                    world.start()
                except worlds.WorldStartFailed as err:
                    print("\t\t", "FAILURE:", world.name())
                else:
                    print("\t\t", world.name())
        return None

    def uninstall(self):
        """
        Uninstalls the server.

        This is more a dialog than a simple command. The user has to choose
        a new server that should run the currently powered worlds.

        See also:
            * ServerWrapper.uninstall()
        """
        print("{} - uninstall:".format(self._server.name()))

        # Replacement
        # ^^^^^^^^^^^
        
        # We need a server that can replace this one.
        other_server_names = self._app.server.get_names()
        other_server_names.pop(other_server_names.index(self._server.name()))

        # Break if there is no other server available.
        if not other_server_names:
            print("\t", "FAILURE: There is no server, that can replace this one.")
            return None

        # Let the user choose the new server.
        tmp = userinput.choose(
            prompt = "Which server should replace this one?",
            choices = other_server_names
            )
        new_server_name = other_server_names[tmp[0]]
        new_server = self._app.server.get(new_server_name)
        
        # Final question
        # ^^^^^^^^^^^^^^

        if not userinput.ask("Are you sure, that you want to uninstall the server?"):
            return None

        # Uninstall
        # ^^^^^^^^^
        
        try:
            self._server.uninstall(new_server)
        except server_wrapper.ServerIsOnlineError as error:
            print("\t", "FAILURE: The server is still online.")
        return None

    
class Server(BasePlugin):
    """
    Command line interface for the EMSM ServerWrapper.
    """

    version = "2.0.0"
    
    def __init__(self, application, name):
        """
        """
        BasePlugin.__init__(self, application, name)

        self.setup_conf()
        self.setup_argparser()
        return None

    def setup_conf(self):
        """
        Copies the configuration options in the object's attributes and
        validates them.
        """
        conf = self.conf()
        
        self._update_message = conf.get(
            "update_message", "The server is going down for an update."
            )

        # Write the configuration options back into the dictionary.
        # Note, that this will initalise the configuration section of this
        # plugin.
        conf["update_message"] = self._update_message
        return None

    def setup_argparser(self):
        """
        Sets the argument parser of this plugin up.
        """
        parser = self.argparser()
        
        parser.description = "Manage your server executables"
                
        parser.add_argument(
            "--configuration",
            action = "count",
            dest = "conf",
            help = "Prints the configuration of the server."
            )

        parser.add_argument(
            "--status",
            action = "count",
            dest = "status",
            help = "Prints the names of the worlds, run by this server."
            )

        update_group = parser.add_mutually_exclusive_group()
        update_group.add_argument(
            "--update",
            action = "count",
            dest = "update",
            help = "Updates the selected server."
            )
        update_group.add_argument(
            "--force-update",
            action = "count",
            dest = "force_update",
            help = "Forces the stop of a world before the update begins."
            )
        
        parser.add_argument(
            "--uninstall",
            action = "count",
            dest = "uninstall",
            help = "Removes the server."
            )
        return None

    def run(self, args):
        """
        ...
        """
        for server in self.app().server().get_selected():            
            server = MyServer(self.app(), server)

            # configuration
            if args.conf:
                server.print_conf()

            # status
            if args.status:
                server.print_status()

            # update
            if args.update:
                server.update(
                    force_stop=False,
                    stop_message=self._update_message
                    )
            elif args.force_update:
                server.update(
                    force_stop=True,
                    stop_message=self._update_message
                    )

            # installation / uninstallation
            if args.uninstall:
                server.uninstall()
        return None
