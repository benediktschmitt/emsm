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
import os
import shlex
import shutil
import urllib.request

# third party
import blinker

# local
import app_lib.downloadreporthook


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
    
if hasattr(shutil, "which"):
    _JAVA = shutil.which("java")
else:
    _JAVA = "java"

try:
    FileNotFoundError
except:
    FileNotFoundError = OSError

    
# Data
# ------------------------------------------------
__all__ = ["ServerError", "ServerUpdateFailure",
           "ServerStatusError", "ServerIsOnlineError",
           "ServerIsOfflineError", "BaseServerWrapper"
           "ServerWrapper", "ServerManager"]


# Exceptions
# --------------------------------------------------
class ServerError(Exception):
    """ Base class for all module exceptions. """
    pass


class ServerUpdateFailure(ServerError):
    """
    Raised if the update of a server failed.
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
class BaseServerWrapper(object):    
    """
    Wraps a minecraft server (file).

    I tried to keep this class as much emsm-independant as possible.
    """
       
    def __init__(self,
                 server,
                 url,
                 name,
                 start_cmd,
                 auto_install=True,
                 ):
        """ ============ ===========================================
            parameter    description
            ============ ===========================================
            server       The path of the server.
            url          The download url of the server.
            name         The name of the server in the application.
            auto_install Downloads the server-file if not yet done.
            start_cmd    The os command to start the server.
                         E.g.: "java -Xmx512M -jar ${server} nogui."
                         Note, that in this example, "${server}" is
                         replaced with the value of *server*.
            ============ ===========================================            
        """
        if name is None:
            name = os.path.basename(server)
            
        self.server = server
        self.name = name
        self.url = url
        self.start_cmd = start_cmd

        # Download the server if not yet done.
        if auto_install and not os.path.exists(self.server):
            self.update()
        return None

    def is_online(self):
        """
        Returns None per default. None means not implemented.
        
        Should be overwritten.
        """
        return None    
    
    def get_start_cmd(self):
        """
        Returns the command to start the server.       
        """
        # In server.conf:
        #
        #   [vanilla]
        #   ...
        #   server = minecraft_server.jar
        #   start_cmd = java -jar {server} nogui.
        #
        # start_args expands to:
        #   "java -jar emsm_root/server/minecraft_server.jar nogui."
        cmd = self.start_cmd.format(
            server = shlex.quote(self.server)
            )
        return cmd

    def update(self, reporthook=None):
        """
        Downloads the server_jar into a temporary file and copies the
        file if the download succeeded to the server directory.
        reporthook is the reporthook of urllib.request.urlretrieve.

        Raises: ServerIsOnlineError, ServerUpdateFailure
        """
        if self.is_online():
            raise ServerIsOnlineError(self)

        try:
            temp_server_file, http_message = urllib.request.urlretrieve(
                self.url,
                reporthook=reporthook
                )
        except (OSError, urllib.error.URLError):
            raise ServerUpdateFailure(self)
        else:
            shutil.move(temp_server_file, self.server)
        return None    

    def uninstall(self):
        """
        Removes the server file.

        Raises: ServerIsOnlineError
        """
        if self.is_online():
            raise ServerIsOnlineError(self)
        
        try:
            os.remove(self.server)
        except FileNotFoundError:
            pass
        return None


class ServerWrapper(BaseServerWrapper):
    """
    This server wrapper is configurable and implements some events.
    """

    # Emmited when the server is uninstalled.
    server_uninstalled = blinker.signal("server_uninstalled")

    def __init__(self, app, name):
        """
        application is a reference to the running application.

        Note, that *application.conf.server[name]* contains the configuration
        of this server wrapper:
            [name]
            server = minecraft_server.jar
            url = https://s3.amazonaws.com/Minecraft.Download/versions/1.6.2/minecraft_server.1.6.2.jar
            start_args = nogui.
        """
        self._app = app
        self.conf = app.conf.server[name]
        
        # Read all other values from the configuration.        
        BaseServerWrapper.__init__(
            self,
            server = os.path.join(app.paths.server_dir, self.conf["server"]),
            url = self.conf["url"],
            name = name,
            start_cmd = self.conf["start_cmd"],
            auto_install = True
            )
        return None

    def is_online(self):
        """
        Returns true if the server is running at least one world. The return
        value is invalid, if the user changed the configuration options,
        associated with this server.
        """
        worlds = self._app.worlds
        running_worlds = worlds.get_by_pred(
            lambda w: w.server is self and w.is_online()
            )
        return bool(running_worlds)

    def update(self, reporthook=None):
        """
        The same magic as in BaseServerWrapper.update(...), but this one will
        print a pretty reporthook.
        """
        if reporthook is None:
            reporthook = app_lib.downloadreporthook.Reporthook(
                self.url, target=self.server)
        BaseServerWrapper.update(self, reporthook)
        return None

    def uninstall(self, replace_with):
        """
        Removes the file and the configuration of the server.

        replace_with has to be another server wrapper. This is necessary
        to avoid errors at runtime.

        Raises: ValueError, TypeError, ServerIsOnline
        """
        if replace_with is self:
            raise ValueError("replace_with has to be another ServerWrapper!")
        if not isinstance(replace_with, type(self)):
            raise TypeError("replace_with has to be a ServerWrapper!")

        # Check if this server is still running some worlds and
        # if all worlds are offline, replace their ServerWrapper.
        worlds = self._app.worlds.get_by_pred(lambda w: w.server is self)
        
        for world in worlds:
            if world.is_online():
                msg = "The world '{}' is online.".format(world.name)
                raise ServerIsOnlineError(self, msg)
            
        for world in worlds:
            world.server = replace_with

        # Let the base class remove the server.
        BaseServerWrapper.uninstall(self)

        # Adapt the configuration files:
        # XXX Don't change the worlds.conf *file* with the world.conf
        #   *attribute* of the WorldWrapper class. This will not overwrite
        #   the default value in the configuration! We have to manipulate the
        #   configuration direct.
        conf = self._app.conf.server
        conf.remove_section(self.name)

        # The default_section is ususually the first secction_name, that
        # is returned.
        conf = self._app.conf.worlds
        for section in conf:
            if "server" not in conf[section]:
                continue
            if conf[section]["server"] == self.name:
                conf[section]["server"] = replace_with.name

        ServerWrapper.server_uninstalled.send(self)
        return None


class ServerManager(object):
    """
    Container for all server wrappers.

    Note: This class makes use of the reference to the
        application.
    """

    def __init__(self, app):
        self._app = app

        # Maps the server names to the ServerWrapper instance
        # server.name => server
        self._server = dict()

        ServerWrapper.server_uninstalled.connect(self._remove)
        return None

    def load(self):
        """
        Loads all server declared in the server configuration file.
        """
        conf = self._app.conf.server
        for section in conf.sections():
            server = ServerWrapper(self._app, section)
            self._server[server.name] = server
        return None

    # container
    # --------------------------------------------

    def _remove(self, server):
        if server in self._server:
            del self._server[server.name]
        return None

    def get(self, servername):
        return self._server[servername]

    def get_all(self):
        return list(self._server.values())

    def get_by_pred(self, pred=None):
        return list(filter(pred, self._server.values()))

    def get_selected(self):
        """
        Returns all server that have been selected per command line argument.
        """
        args = self._app.argparser.args
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
