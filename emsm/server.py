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
import subprocess
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
           "ServerInstallationFailure",
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


class ServerInstallationFailure(ServerError):
    """
    Raised if a server installation failed.
    """

    def __init__(self, server, msg=None):
        self.server = server
        self.msg = str(msg)
        return None

    def __str__(self):
        temp = "The installation of the server '{}' failed."\
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
        self.msg = str(msg)
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
        **ABSTRACT**
        
        The unique name of the server.

        **Example**:

        ``"vanilla 1.8"``
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

        # The configuration section in the *server.conf* configuration file.
        # Note, that only a server wrapper which has a name, is listed in
        # the configuration.
        try:
            self.name()
        except NotImplementedError:
            self._conf = None
        else:
            if not app.conf().server().has_section(self.name()):
                app.conf().server().add_section(self.name())
            self._conf = app.conf().server()[self.name()]
        return None

    def server(self):
        """
        Absolute path of the server executable.
        """
        return self._server

    def conf(self):
        """
        Returns the configuration section in the *server.conf* configuration
        file.
        """
        return self._conf
    
    def default_url(self):
        """
        **ABSTRACT**

        The URL where the server executable can be downloaded from.
        """
        raise NotImplementedError()
    
    def url(self):
        """
        Returns the url in :meth:`conf`, if available. Otherwise the value
        of :meth:`default_url`.
        """
        if "url" in self._conf:
            return self._conf.get("url")
        return self.default_url()
        
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
        **ABSTRACT**

        Installs the server by downloading it to :meth:`server`. If the
        server is already installed, nothing should happen.

        This method is called during the EMSM start phase if
        :meth:`is_installed` returns ``False``.

        :raises ServerInstallationFailure:
            * when the installation failed.
        """
        raise NotImplementedError()
    
    def default_start_cmd(self):
        """
        **ABSTRACT**
        
        Returns the bash command string, that must be executed, to start the
        server.

        If there are paths in the returned command, they must be absolute.
        """
        raise NotImplementedError()   
    
    def start_cmd(self):
        """
        Returns the value for *start_command* in :meth:`conf` if available
        and the :meth:`default_start_cmd` otherwise.
        """
        if "start_command" in self._conf:
            cmd = self._conf.get("start_command")\
                  .format(server_path=shlex.quote(self._server))
            return cmd
        else:
            return self.default_start_cmd()

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

    def default_start_cmd(self):
        return "java -jar {} nogui.".format(shlex.quote(self._server))

    def translate_command(self, cmd):
        return cmd

    def install(self):
        """
        """
        if self.is_installed():
            return None
        
        # Simply download the minecraft jar from mojang and copy the .jar in
        # the EMSM_ROOT/server directory.
        try:
            tmp_path, http_resp = urllib.request.urlretrieve(self.url())
        except Exception as err:
            raise ServerInstallationFailure(self, err)
        else:
            shutil.move(tmp_path, self.server())
        return None
    
    
class Vanilla_1_2(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.2"

    def default_url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.2.5/minecraft_server.1.2.5.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.2.*")


class Vanilla_1_3(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.3"

    def default_url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.3.2/minecraft_server.1.3.2.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.3.*")


class Vanilla_1_4(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.4"

    def default_url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.4.7/minecraft_server.1.4.7.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.4.*")


class Vanilla_1_5(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.5"

    def default_url(self):
        return "http://s3.amazonaws.com/Minecraft.Download/versions/1.5.2/minecraft_server.1.5.2.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.5.*")


class Vanilla_1_6(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.6"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar"
    
    def log_path(self):
        return "./server.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.6.*")


class Vanilla_1_7(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.7"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.7.10/minecraft_server.1.7.10.jar"
    
    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.7.*")


class Vanilla_1_8(VanillaBase):
    
    @classmethod
    def name(self):
        return "vanilla 1.8"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.8/minecraft_server.1.8.jar"
    
    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.8.*")


# MinecraftForger
# '''''''''''''''


class MinecraftForgeBase(BaseServerWrapper):
    """
    Base class for the minecraft forge server.
    """

    def translate_command(self, cmd):
        return cmd

    def install(self):
        """
        """
        if self.is_installed():
            return None
        
        try:
            # We need to download the *installer* first.
            try:
                tmp_path, http_resp = urllib.request.urlretrieve(self.url())
            except Exception as err:
                raise ServerInstallationFailure(err)
            else:
                
                # Now, we have to run the installer.
                if os.path.exists(self.server()):
                    shutil.rmtree(self.server())            
                os.makedirs(self.server())
                
                os.chdir(self.server())
                if not os.path.samefile(self.server(), os.curdir):
                    msg = "Could not chdir to {}".format(self.server())
                    raise ServerInstallationFailure(self, msg)

                sys_install_cmd = "java -jar {} --installServer"\
                                      .format(tmp_path)
                sys_install_cmd = shlex.split(sys_install_cmd)
                try:
                    p = subprocess.Popen(
                        sys_install_cmd,
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE
                        )

                    # Store the output of the installer in the logfiles.
                    out, err = p.communicate()
                    out = out.decode()
                    err = err.decode()
                    log.info(out)

                    # Check, if the installer exited with return code 0 and
                    # throw an exception if not.
                    if p.returncode:
                        msg = "Installer returned with '{}'."\
                              .format(p.returncode)
                        raise ServerInstallationFailure(self, msg)
                except Exception as err:
                    raise ServerInstallationFailure(self, err)
        except:
            # Try to undo the installation.
            if os.path.exists(self.server()):
                shutil.rmtree(self.server())
        return None


class MinecraftForge_1_6(MinecraftForgeBase, Vanilla_1_6):

    @classmethod
    def name(self):
        return "minecraft forge 1.6"

    def default_url(self):
        return "http://files.minecraftforge.net/minecraftforge/minecraftforge-installer-1.6.4-9.11.1.916.jar"

    def default_start_cmd(self):
        filenames = [filename \
                     for filename in os.listdir(self.server()) \
                     if re.match("^minecraftforge-universal-1\.6.*.jar$", filename)]
        filename = filenames[0]
        
        start_cmd =  "java -jar {} nogui."\
                    .format(shlex.quote(os.path.join(self._server, filename)))
        return start_cmd
    
            
class MinecraftForge_1_7(MinecraftForgeBase, Vanilla_1_7):

    @classmethod
    def name(self):
        return "minecraft forge 1.7"

    def default_url(self):
        return "http://files.minecraftforge.net/maven/net/minecraftforge/forge/1.7.10-10.13.0.1180/forge-1.7.10-10.13.0.1180-installer.jar"

    def default_start_cmd(self):
        filenames = [filename \
                     for filename in os.listdir(self.server()) \
                     if re.match("^forge-1\.7.*.jar$", filename)]
        filename = filenames[0]
        
        start_cmd =  "java -jar {} nogui."\
                    .format(shlex.quote(os.path.join(self._server, filename)))
        return start_cmd
    

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

    def default_url(self):
        return "http://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar"

    def install(self):
        """
        """
        if self.is_installed():
            return None
        
        # Simply download the latest build and save it in the EMSM_ROOT/server
        # directory.
        try:
            tmp_path, http_resp = urllib.request.urlretrieve(self.url())
        except Exception as err:
            raise ServerInstallationFailure(err)
        else:
            shutil.move(tmp_path, self.server())
        return None

    def default_start_cmd(self):
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
        self.__add_emsm_wrapper()
        return None

    def __add_emsm_wrapper(self):
        """
        Loads all default EMSM server wrappers. These are all server wrappers
        defined in this module.
        """
        # We only add the complete wrappers. These wrappers have all
        # virtual (abstract) methods implemented.
        wrappers = [
            Vanilla_1_2,
            Vanilla_1_3,
            Vanilla_1_4,
            Vanilla_1_5,
            Vanilla_1_6,
            Vanilla_1_7,
            Vanilla_1_8,
            MinecraftForge_1_6,
            MinecraftForge_1_7,
            BungeeCordServerWrapper,
            ]

        for wrapper in wrappers:
            self.add(wrapper)
        return None

    def add(self, server_class):
        """
        Makes the *server_class* visible to this manager. The class
        must implement all abstract methods of :class:`BaseServerWrapper` or
        unexpected errors may occure.

        :raises TypeError:
            if *server_class* does not inherit :class:`BaseServerWrapper`
        :raises ValueError:
            if another wrapper with the :meth:`~BaseServerWrapper.name()` of
            *server_class* has already been registered.
        """
        if not issubclass(server_class, BaseServerWrapper):
            raise TypeError("server_class has to inherit from BaseServerWrapper")

        if server_class.name() in self._server:
            raise ValueError("another server with the name '{}' has already "\
                             "been registered.".format(server_class.name()))

        # Create a new instance of the server wrapper.
        self._server[server_class.name()] = server_class(self._app)
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
