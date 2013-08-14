#!/usr/bin/env python3


# Modules
# ------------------------------------------------
# local
import base_world_wrapper
from base_world_wrapper import *


# Data
# ------------------------------------------------
# Not nice, but I want the base_world_wrapper
# to be an application independent module.
__all__ = base_world_wrapper.__all__[:]
__all__.append("WorldWrapper")


# Classes
# ------------------------------------------------
class WorldWrapper(BaseWorldWrapper):
    """
    This world wrapper uses the world configuration to get the
    values for parameters in some methods.

    Events:
    "world_status_change_required", #(self, current_status, target_status)
    "world_status_change_complete", #(self, current_status, target_status)
    "world_status_change_failed",   #(self, current_status, target_status, error)
    "world_uninstalled",            #(self)
    """

    def __init__(self, application, name):
        """
        application is a reference to the running application.

        conf is a dictionary, that contains the configuration
        of this world:
            port = <auto> or int
            min_ram = int
            max_ram = int
            stop_timeout = int
            stop_message = string
            stop_delay = int
            server = str
        """
        self._application = application
        self.conf = application.configuration.worlds[name]

        server_manager = application.server_manager
        self.server_wrapper = server_manager.get_server(self.conf["server"])

        # Events
        add_event = application.event_dispatcher.add_signal
        events = ["world_status_change_required", #(self, current_status, target_status)
                  "world_status_change_complete", #(self, current_status, target_status)
                  "world_status_change_failed",   #(self, current_status, target_status, error)
                  "world_uninstalled",            #(self)
                  ]
        self.events = {event: add_event(event) for event in events}

        directory = application.pathsystem.get_world_dir(name)
        BaseWorldWrapper.__init__(self, name, directory)
        return None

    # setup
    # --------------------------------------------

    def uninstall(self):
        """
        Removes the world's directory and the configuration
        of the world.
        When done, emits the "world_uninstalled" signal.
        """
        BaseWorldWrapper.uninstall(self)

        worlds_conf = self._application.configuration.worlds
        worlds_conf.remove_section(self.name)

        self.events["world_uninstalled"].emit(self)
        return None

    # start / stop
    # --------------------------------------------

    def _perform_status_change(self, func, end_status):
        """
        Emits the signals that signalises a status change of
        this world before and after changing the status.
        """
        original_status = self.is_online()

        self.events["world_status_change_required"].emit(
            self, original_status, end_status)

        try:
            ret = func()
        except WorldError as error:
            self.events["world_status_change_failed"].emit(
                self, original_status, end_status, error)
            raise error
        else:
            self.events["world_status_change_complete"].emit(
                self, original_status, end_status)
            return ret

    def start(self):
        """
        Starts the world.
        """
        start_cmd = self.server_wrapper.get_start_cmd(
            int(self.conf["min_ram"]), int(self.conf["max_ram"]))
        init_properties = {"server-port": self.conf["port"]}

        func = lambda: BaseWorldWrapper.start(self, start_cmd, init_properties)
        return self._perform_status_change(func, True)

    def kill_processes(self):
        """
        Kills the processes of the world.
        """
        func = lambda: BaseWorldWrapper.kill_processes(self)
        return self._perform_status_change(func, False)


    def stop(self, force_stop=False):
        """
        Stops the world.
        """
        message = self.conf["stop_message"]
        timeout = int(self.conf["stop_timeout"])
        delay = int(self.conf["stop_delay"])

        func = lambda: BaseWorldWrapper.stop(self, message,
                                             delay, timeout, force_stop)
        return self._perform_status_change(func, False)