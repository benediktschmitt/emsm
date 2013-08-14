#!/usr/bin/env python3


# Modules
# ------------------------------------------------
from world_wrapper import WorldWrapper


# Data
# ------------------------------------------------
__all__ = ["WorldManager"]


# Classes
# ------------------------------------------------
class WorldManager(object):
    """
    Works as container for the worlds.

    """

    def __init__(self, application):
        self._application = application

        # Maps the name of the world to the world wrapper
        # world.name => world
        self._worlds = dict()

        self._application.event_dispatcher.connect(
            self._remove_world, "world_uninstalled", create=True)
        return None

    def load_worlds(self):
        """
        Loads all worlds declared in the configuration file.
        """
        conf = self._application.configuration.worlds

        for section in conf.sections():
            world = WorldWrapper(self._application, section)
            self._worlds[world.name] = world
        return None

    # container
    # --------------------------------------------

    def _remove_world(self, world):
        if world in self._worlds:
            del self._worlds[world.name]
        return None

    def get_world(self, worldname):
        return self._worlds[worldname]

    def get_all_worlds(self):
        return list(self._worlds.values())

    def get_filtered_worlds(self, func=None):
        """
        Returns the worlds where func returns true.
        E.g.:
        func = lambda w: w.is_running()
        """
        return list(filter(func, self._worlds.values()))

    def get_selected_worlds(self):
        """
        Returns all worlds that have been selected by the
        command line arguments.
        """
        argparser = self._application.argparser
        args = argparser.args

        selected_worlds = args.worlds
        all_worlds = args.all_worlds

        if args.all_worlds:
            return list(self._worlds.values())
        else:
            return [self._worlds[world] for world in selected_worlds]

    def get_available_worlds(self):
        """
        Returns a list with the names of all worlds.
        """
        return list(self._worlds)