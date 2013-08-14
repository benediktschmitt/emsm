#!/usr/bin/env python3


# Modules
# ------------------------------------------------
from server_wrapper import ServerWrapper


# Data
# ------------------------------------------------
__all__ = ["ServerManager"]


# Classes
# ------------------------------------------------
class ServerManager(object):
    """
    Container for all server wrappers.

    Note: This class makes use of the reference to the
        application.
    """

    def __init__(self, application):
        self._application = application

        # Maps the server names to the server wrapper
        # server.name => server
        self._server = dict()

        self._application.event_dispatcher.connect(
            self._remove_server, "server_uninstalled", create=True)
        return None

    def load_server(self):
        """
        Loads all server declared in the server configuration file.
        """
        conf = self._application.configuration.server

        for section in conf.sections():
            server = ServerWrapper(self._application, section)
            self._server[server.name] = server
        return None

    # container
    # --------------------------------------------

    def _remove_server(self, server):
        if server in self._server:
            del self._server[server.name]
        return None

    def get_server(self, servername):
        return self._server[servername]

    def get_all_server(self):
        return list(self._server.values())

    def get_available_server(self):
        """
        Returns a list with the names of all server.
        """
        return list(self._server)