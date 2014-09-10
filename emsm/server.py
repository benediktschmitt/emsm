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
import re

# third party
import blinker


# Backward compatibility
# --------------------------------------------------

if not hasattr(shlex, "quote"):
    # From the Python3.3 library
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
           "BaseServerWrapper",
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

    def __init__(self, server, msg=None):
        self.server = server
        self.msg = msg
        return None

    def __str__(self):
        temp = "The update of the server '{}' failed."\
               .format(self.server.name())
        if self.msg is not None:
            temp += " " + self.msg
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
    Wraps a minecraft server (executable), NOT a world.

    The BaseServerWrapper is initialized using the options in the
    :file:`server.conf` configuration file.

    :param emsm.application.Application app:
        The parent EMSM application
    """

    @classmethod
    def name(self):
        """
        The unique name of the server.

        **Example**:

        ``"vanilla 1.8"``

        **Override**:

        in subclasses.
        """
        raise NotImplementedError()

    @classmethod
    def url(self):
        """
        The URL where the server executable can be downloaded from.

        **Override:**

        in subclases
        """
        raise NotImplementedError()
    
    def __init__(self, app):
        """
        """
        # This class is abstract and can not be initialised.
        if type(self) is BaseServerWrapper:
            raise RuntimeError("BaseServerWrapper is an abstract class")            
            
        log.info("initialising server '{}' ...".format(self.name()))
        
        self._app = app

        # The absolute path to the server executable that is
        # wrapped by this object.
        # The filename is simply *name*.
        self._server = os.path.join(app.paths().server_dir(), self.name())
        return None

    def server(self):
        """
        Absolute path of the server executable.
        """
        return self._server
        
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

        # Download the server.
        log.info("downloading server '{}' from '{}' ..."\
                 .format(type(self).name(), type(self).url())
                 )
        try:
            temp_server_file, http_message = urllib.request.urlretrieve(
                type(self).url(),
                )
        except:
            pass
        else:
            shutil.move(temp_server_file, self._server)
            log.info("downloaded server '{}'.".format(type(self).name()))
        return None

    def start_cmd(self):
        """
        **ABSTRACT**
        
        Returns the bash command string, that must be executed, to start the
        server.

        If there are paths in the returned command, they must be absolute.
        """
        raise NotImplementedError()

    def translate_command(self, cmd):
        """
        **ABSTRACT**
        
        Translates the vanilla server command *cmd* to a command with the same
        meaning, but which can be understood by the server.

        **Example:**

            .. code-block:: python

                >>> # A BungeeCoord wrapper would do this:
                >>> bungeecord.translate_command("stop")
                "end"
                >>> bungeecord.translate_command("say Hello World!")
                "alert Hello World!"
        """
        return NotImplementedError()

    def log_path(cls, self):
        """
        **ABSTRACT**
        
        Returns the path of the server log file of a world.

        If a relative path is returned, the base path is the world
        directory.
        """
        raise NotImplementedError()

    def log_start_re(self):
        """
        **ABSTRACT**
        
        Returns a regex, that matches the first line in the log file,
        after a server restart.
        """
        raise NotImplementedError()
    

# Vanilla
# '''''''

class VanillaBase(BaseServerWrapper):
    """
    Base class for all vanilla server versions.
    """

    def start_cmd(self):
        return "java -jar {} nogui.".format(shlex.quote(self._server))

    def translate_command(self, cmd):
        return cmd
    
    
class Vanilla_1_2(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.2"

    @classmethod
    def url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.2.5/minecraft_server.1.2.5.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.2.*")


class Vanilla_1_3(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.3"

    @classmethod
    def url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.3.2/minecraft_server.1.3.2.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.3.*")


class Vanilla_1_4(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.4"

    @classmethod
    def url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.4.7/minecraft_server.1.4.7.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.4.*")


class Vanilla_1_5(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.5"

    @classmethod
    def url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.5.2/minecraft_server.1.5.2.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.5.*")


class Vanilla_1_6(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.6"

    @classmethod
    def url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.6.*")


class Vanilla_1_7(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.7"

    @classmethod
    def url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.7.10/minecraft_server.1.7.10.jar"
    
    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.7.*")


class Vanilla_1_8(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.8"

    @classmethod
    def url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.8/minecraft_server.1.8.jar"
    
    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.8.*")


# Craftbukkit
# '''''''''''

class BukkitBase(BaseServerWrapper):

    def start_cmd(self):
        return "java -jar {}".format(shlex.quote(self._server))

    def translate_command(self, cmd):
        return cmd

# Bungeecord
# ''''''''''

class BungeeCordServerWrapper(BaseServerWrapper):
    """
    Wraps only the **latest** BungeeCord version.

    Unfortunetly, the BungeeCord server uses the git commit hash value
    as its version number. So it would be too many work to keep track of the
    versions.
    """

    @classmethod
    def name(self):
        return "bungeecord"

    @classmethod
    def url(self):
        return "http://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar"

    def start_cmd(self):
        return "java -jar {}".format(shlex.quote(self._server))
    
    def translate_command(self, cmd):
        cmd = cmd.strip()
        if cmd.startswith("say "):
            cmd = "alert " + cmd[len("say "):]
        elif cmd == "stop":
            cmd = "end"
        return cmd

    def log_path(self):
        return "./proxy.log.0"

    def log_start_re(self):
        return re.compile("^.*Enabled BungeeCord version git:.*")


# MC-Server
# '''''''''

class MCServer(BaseServerWrapper):
    pass


# Server DB
# ------------------------------------------------

class ServerManager(object):
    """
    Manages all server wrappers, owned by an EMSM application.

    The ServerManager helps to avoid double instances of the same server
    wrapper.
    """

    def __init__(self, app):
        """
        """
        self._app = app
        
        # Maps *server.name()* to *server*
        self._server = dict()
        self._load()
        return None

    def _load(self):
        """
        Loads all subclasses of BaseServerWrapper in ``self._server_cls``.
        """
        for cls in globals().values():
            if type(cls).__name__ != "type"\
               or not issubclass(cls, BaseServerWrapper):
                continue

            try:
                name = cls.name()
            except NotImplementedError as err:
                pass
            else:
                self._server[name] = cls(self._app)
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
