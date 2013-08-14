#!/usr/bin/env python


# Modules
# ------------------------------------------------
import os

# local
import base_server_wrapper
from base_server_wrapper import *


# Data
# ------------------------------------------------
# Not nice, but I want the base_server_wrapper
# to be an application independent module.
__all__ = base_server_wrapper.__all__[:]
__all__.append("ServerWrapper")


# Classes
# ------------------------------------------------
class ServerWrapper(BaseServerWrapper):
    """
    This server wrapper is configurable and implements
    some events.

    Note: This class makes heavy use of the reference
        to the application.

    Events:
    "server_uninstalled", #(self)
    """

    def __init__(self, application, name):
        """
        application is a reference to the running application.

        conf is a dictionary, that contains the configuration
        of this server:
            [name]
            server = minecraft_server.jar
            url = https://s3.amazonaws.com/Minecraft.Download/versions/1.6.2/minecraft_server.1.6.2.jar
            start_args = nogui.
        """
        self._application = application
        self.conf = application.configuration.server[name]

        # Events
        add_event = application.event_dispatcher.add_signal
        events = ["server_uninstalled", #(self)
                  ]
        self.events = {event : add_event(event) for event in events}

        server = os.path.join(
            application.pathsystem.server_dir, self.conf["server"])
        BaseServerWrapper.__init__(
            self, server, self.conf["url"], self.conf["start_args"],
            name, auto_install=True)
        return None

    def is_online(self):
        """
        Returns true if the server is running at least one world.
        """
        world_manager = self._application.world_manager
        worlds = world_manager.get_filtered_worlds(
            lambda w: w.is_online() and w.server_wrapper is self
            )
        return bool(worlds)

    def uninstall(self, replace_with):
        """
        Removes the file and the configuration of the server.

        replace_with has to be another server wrapper. This is necessary
        to avoid errors at runtime.

        Raises: ServerIsOnline
        """
        if replace_with is self:
            raise ValueError("replace_with has to be another server wrapper!")
        if type(replace_with) != type(self):
            raise TypeError("replace_with has to be a server wrapper!")

        # Reconfigure the worlds that are running this server.
        worlds = self._application.world_manager.get_all_worlds()
        for world in worlds:
            if world.server_wrapper is not self:
                continue
            if world.is_online():
                msg = "The world '{}' is online.".format(world.name)
                raise ServerIsOnlineError(self, msg)
            world.server_wrapper = replace_with

        BaseServerWrapper.uninstall(self)

        # Adapt the configuration files:
        # XXX Don't change the worlds.conf with the world.conf
        #   attribute. This will not overwrite the default value
        #   in the configuration!
        conf = self._application.configuration.server
        conf.remove_section(self.name)

        conf = self._application.configuration.worlds
        for section in conf:
            if "server" not in conf[section]:
                continue
            if conf[section]["server"] == self.name:
                conf[section]["server"] = replace_with.name

        self.events["server_uninstalled"].emit(self)
        return None
