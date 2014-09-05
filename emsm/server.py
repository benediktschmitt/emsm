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

# std
import os
import shlex
import shutil
import urllib.request
import logging

# third party
import blinker


# Backward compatibility
# --------------------------------------------------

if not hasattr(shlex, "quote"):
    # From the Python3.3 library
    import re
    _find_unsafe = re.compile(r'[^\w@%+=:,./-]', re.ASCII).search
    def _shlex_quote(s):
        """Return a shell-escaped version of the string *s*."""
        if not s:
            return "''"
        if _find_unsafe(s) is None:
            return s

        # use single quotes, and put single quotes into double quotes
        # the string $'b is then quoted as '$'"'"'b'
        return "'" + s.replace("'", "'\"'\"'") + "'"
    shlex.quote = _shlex_quote
    del re
    
try:
    FileNotFoundError
except:
    FileNotFoundError = OSError

    
# Data
# ------------------------------------------------

__all__ = ["ServerError",
           "ServerUpdateFailure",
           "ServerStatusError",
           "ServerIsOnlineError",
           "ServerIsOfflineError",
           "ServerWrapper",
           "ServerManager"
           ]

log = logging.getLogger(__file__)


# Exceptions
# --------------------------------------------------

class ServerError(Exception):
    """
    Base class for all exceptions in this module.
    """
    pass


class ServerUpdateFailure(ServerError):
    """
    Raised if a server update failed.
    """

    def __init__(self, server):
        self.server = server
        return None

    def __str__(self):
        temp = "The update of the server '{}' failed."\
               .format(self.server.name)
        return temp

    
class ServerStatusError(ServerError):
    """
    Raised if the server should be online/offline
    for an action but is offline/online.
    """

    def __init__(self, server, status, msg = str()):
        self.server = server
        self.status = status
        self.msg = msg
        return None

    def __str__(self):
        if self.status:
            temp = "The server '{}' is online. {}"
        else:
            temp = "The server '{}' is offline. {}"
        temp = temp.format(self.server.name, self.msg)
        return temp    


class ServerIsOnlineError(ServerStatusError):
    """
    Raised if the server is online but should be offline.
    """
    
    def __init__(self, server, msg = str()):
        ServerStatusError.__init__(self, server, True, msg)
        return None

    
class ServerIsOfflineError(ServerStatusError):
    """
    Raised if the server is offline but should be online.
    """

    def __init__(self, server, msg = str()):
        ServerStatusError.__init__(self, server, False, msg)
        return None

    
# Classes
# ------------------------------------------------

class ServerWrapper(object):    
    """
    Wraps a minecraft server (executable), NOT a world.

    The ServerWrapper is initialized using the options in the
    :file:`server.conf` configuration file.

    :param emsm.application.Application app:
        The parent EMSM application
    :param str name:
        The name of the server in the :file:`server.conf` configuration
        file.

    .. seealso::

        * :class:`emsm.conf.ServerConfiguration`
    """

    #: Signal that is emitted, when a server has been uninstalled.
    server_uninstalled = blinker.signal("server_uninstalled")
    

    def __init__(self, app, name):
        """
        """
        log.info("initialising server '{}' ...".format(name))
        
        self._app = app
        self._conf = app.conf().server()[name]
        self._check_conf()

        # The absolute path to the server executable that is
        # wrapped by this object.
        self._server = os.path.join(
            app.paths().server_dir(), self._conf["server"]
            )

        # The name of the server executable.
        self._name = name

        # The download url of the server.
        self._url = self._conf["url"]

        # The shell command which starts the server.
        # This string contains still some placeholders.
        #
        # See also:
        #   * start_cmd()
        self._raw_start_cmd = self._conf["start_cmd"]
        return None

    def _check_conf(self):
        """
        Validates the configuration values.

        .. seealso:
        
            * Application.conf().server()
            * conf()

        :raises ValueError:
            if a configuration option has an invalid value.
        :raises TypeError:
            if a configuration option has an invalid type.
        """
        # server
        if not "server" in self._conf:
            raise KeyError("conf:server not set")

        # url
        if not "url" in self._conf:
            raise KeyError("conf:url not set")
        
        try:
            urllib.parse.urlparse(self._conf["url"])
        except urllib.error:
            # Todo: Raise a TypeError instead?
            raise ValueError("conf:url is not a url")

        # start_cmd
        if not "start_cmd" in self._conf:
            raise KeyError("conf:start_cmd not set")
        return None

    def conf(self):
        """
        Returns a dictionary like object that contains the configuration of this
        ServerWrapper.
        """
        return self._conf

    def server(self):
        """
        Absolute path of the server executable.
        """
        return self._server

    def name(self):
        """
        The name of the server (configuration section name).
        """
        return self._name

    def url(self):
        """
        The download url of the server.
        """
        return self._url

    def raw_start_cmd(self):
        """
        The raw, unformatted command that starts the server. This may
        still contain placeholders like ``'{server}'``.

        .. seealso::

            * :meth:`start_cmd`
        """
        return self._raw_start_cmd
    
    def start_cmd(self):
        """
        Returns the formatted shell command needed to start the server.

        .. seealso::

            * :meth:`raw_start_cmd`
        """
        # In server.conf:
        #
        #   [vanilla]
        #   ...
        #   server = minecraft_server.jar
        #   start_cmd = java -jar {server} nogui.
        #
        # start_cmd is expanded to:
        #   "java -jar emsm_root/server/minecraft_server.jar nogui."
        cmd = self._raw_start_cmd.format(
            server = shlex.quote(self._server)
            )
        return cmd
    
    def is_installed(self):
        """
        ``True`` if the executable has been downloaded and exists, otherwise
        ``False``.
        """
        return os.path.exists(self._server)
    
    def is_online(self):
        """
        Returns ``True`` if at least one world is currently running with
        this server.
        """
        worlds = self._app.worlds().get_by_pred(
            lambda w: w.server() is self and w.is_online()
            )
        return bool(worlds)

    def update(self, reporthook=None):
        """
        Downloads the server_jar into a temporary file and copies the
        file, if the download was succesful, to the server directory.

        :param reporthook:
            passed to :func:`urllib.request.urlretrieve`.

        :raises ServerIsOnlineError:
            if at least one world is still online using this server.
        :raises ServerUpdateFailure:
            if the download of the server failed.
        """
        if self.is_online():
            raise ServerIsOnlineError(self)

        # Download the server.
        log.info("downloading server '{}' from '{}' ..."\
                 .format(self._name, self._url)
                 )
        try:
            temp_server_file, http_message = urllib.request.urlretrieve(
                self._url,
                reporthook=reporthook
                )
        except (OSError, urllib.error.URLError):
            raise ServerUpdateFailure(self)
        else:
            shutil.move(temp_server_file, self._server)
            log.info("downloaded server '{}'.".format(self._name))
        return None

    def install(self):
        """
        Installs the server which basically means to call :meth:`update` if
        necessairy.
        If the server is already installed, nothing happens.

        :raises ServerUpdateFailure:
            if the download of the server failed.
        """
        if self.is_installed():
            return None

        self.update()
        return None

    def uninstall(self, new_server):
        """
        Removes the server and its configuration. The worlds currently run
        by this server will be powered by *new_server* after the next start.

        The signal :attr:`server_uninstalled` is emitted, when the
        uninstallation is complete.

        :raises ServerIsOnlineError:
        :raises TypeError:
            if *new_server* is not a ServerWrapper instance.
        :raises ValueError:
            if *new_server* is not **another** ServerWrapper instance.                

        .. todo::
        
            This method should not raise a ServerIsOnlineError. It should
            stop all running worlds and restart them with the new server.
        """
        log.info("uninstalling the server '{}' ...".format(self._name))
        
        if self.is_online():
            raise ServerIsOnlineError(self)

        if not new_server is None:
            if not isinstance(new_server, ServerWrapper):
                raise TypeError("*new_server* has to be a ServerWrapper")                
            if new_server is self:
                raise ValueError("*new_server* has to be **another** "
                                 "ServerWrapper")

        # World reconfiguration
        # ^^^^^^^^^^^^^^^^^^^^^

        # Get the worlds which are configured to run with this server.
        worlds = self._app.worlds().get_by_pred(lambda w: w.server() is self)
        for world in worlds:
            # Replace the server wrapper.
            world.set_server(new_server)

        # Remove the server
        # ^^^^^^^^^^^^^^^^^

        # The server file.
        try:
            os.remove(self._server)
        except FileNotFoundError:
            pass

        # The server configuration.
        self._app.conf().server().remove_section(self._name)

        # Finish
        # ^^^^^^

        log.info("uninstalled server '{}'.".format(self._name))
        ServerWrapper.server_uninstalled.send(self)
        return None


class ServerManager(object):
    """
    A container for all :class:`ServerWrapper` used by an EMSM application.
    """

    def __init__(self, app):
        self._app = app

        # Maps the server names to the ServerWrapper instance
        # server.name => server
        self._server = dict()

        ServerWrapper.server_uninstalled.connect(self._remove)
        return None

    def load_server(self):
        """
        Loads all server declared in the server configuration file.

        If a server has not been downloaded yet, :meth:`ServerWrapper.update`
        is called.

        .. seealso::
        
            * :meth:`emsm.application.Application.conf`
            * :meth:`ServerWrapper.is_installed`
            * :meth:`ServerWrapper.install`
        """
        log.info("loading all server wrappers ...")
        
        conf = self._app.conf().server()
        for section in conf.sections():
            server = ServerWrapper(self._app, section)
            self._server[server.name()] = server

            # Install the server if not yet done.
            server.install()
        return None

    # container
    # --------------------------------------------

    def _remove(self, server):
        """
        Removes the :class:`ServerWrapper` *server* from the internal map.
        """
        if server.name() in self._server.values():
            del self._server[server.name()]
        return None

    def get(self, servername):
        """
        Returns the :class:`ServerWrapper` with the name *servername* and
        ``None``, if there is not such a server.
        """
        return self._server.get(servername)

    def get_all(self):
        """
        Returns a list with all loaded :class:`ServerWrapper`.
        """
        return list(self._server.values())

    def get_by_pred(self, pred=None):
        """
        Almost equal to:

        .. code-block:: python
        
            >>> filter(pred, ServerManager.get_all())
            ...
        """
        return list(filter(pred, self._server.values()))

    def get_selected(self):
        """
        Returns all server that have been selected per command line argument.
        """
        args = self._app.argparser().args()
        
        selected_server = args.server
        all_server = args.all_server
        
        if all_server:
            return list(self._server.values())
        else:
            return [self._server[server] for server in selected_server]

    def get_names(self):
        """
        Returns a list with the names of all server.
        """
        return list(self._server.keys())
