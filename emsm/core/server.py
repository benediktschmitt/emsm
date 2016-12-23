#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2014-2016 Benedikt Schmitt <benedikt@benediktschmitt.de>
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
import tempfile
import glob

# third party
import blinker
import yaml


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
        temp = temp.format(self.server.name(), self.msg)
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

    :param emsm.core.application.Application app:
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
        log.info("initialising server '{}' ...".format(self.name()))

        self.__app = app

        # Absolute path to the directory which should contain all server
        # software.
        # For the vanilla server, this is only a single file
        # *minecraft_server.jar*. The forge server comes with some
        # subdirectories and libraries.
        self.__directory = app.paths().server_(self.name())

        # The configuration section in the *server.conf* configuration file.
        if not app.conf().server().has_section(self.name()):
            app.conf().server().add_section(self.name())
        self.__conf = app.conf().server()[self.name()]
        return None

    def directory(self):
        """
        Absolute path to the directory which contains all server software.
        """
        if not os.path.exists(self.__directory):
            os.makedirs(self.__directory)
        return self.__directory

    def exe_path(self):
        """
        **ABSTRACT**

        Absolute path to the server executable. This file is usually located
        in :meth:`directory`.
        """
        raise NotImplementedError()

    def conf(self):
        """
        Returns the configuration section in the *server.conf* configuration
        file.
        """
        return self.__conf

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
        if "url" in self.conf():
            return self.conf().get("url")
        return self.default_url()

    def is_installed(self):
        """
        ``True`` if the executable has been downloaded and exists, otherwise
        ``False``.

        Per default, this method only checks if the :meth:`directory` is empty
        or not. It can be *overridden* for a more detailed check.
        """
        return bool(os.listdir(self.directory()))

    def is_online(self):
        """
        Returns ``True`` if at least one world is currently running with
        this server.
        """
        worlds = self.__app.worlds().get_by_pred(
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

    def reinstall(self):
        """
        Tries to reinstall the server. If the reinstallation fails, the
        old :meth:`server()` is restored and everything is like before.

        :raises ServerInstallationFailure:
            * when the installation failed.
        :raises ServerIsOnlineError:
            * when a world powered by this server software is online.
        """
        if self.is_online():
            raise ServerIsOnlineError(self)

        # Save the old directory in a temporary folder, so that we can restore
        # it if something fails.
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_server_path = shutil.move(self.directory(), tmp_dir)

            # is_installed() returns now False.
            assert not self.is_installed()

            # So we can call install() again.
            try:
                self.install()
            except:
                # Clean up the installation target directory self.directory()
                # and move the old server path back.
                if os.path.exists(self.directory()):
                    if os.path.isdir(self.directory()):
                        shutil.rmtree(self.directory())
                    else:
                        # This is a relict of version 3, when not all server
                        # created a directory in ``server/``.
                        os.remove(self.directory())
                shutil.move(tmp_server_path, self.directory())

                # Reraise the original exception.
                raise
        return None

    def default_start_cmd(self):
        """
        **ABSTRACT**

        Returns the bash command string, that must be executed, to start the
        server.

        If there are paths in the returned command, they must be absolute.
        """
        raise NotImplementedError()

    def start_cmd(self, world=None):
        """
        Returns the value for *start_command* in :meth:`conf` if available
        and the :meth:`default_start_cmd` otherwise.

        :arg str world:
            The name of an EMSM world. The start command can be overridden
            for each world. We will look for a custom start command in the
            worlds configuration file first.
        """
        cmd = ""

        # 1.) morpheus.world.conf
        if world:
            world_conf = self.__app.conf().world(world)
            if world_conf.has_option("server:" + self.name(), "start_command"):
                cmd = world_conf["server:" + self.name()]["start_command"]

        # 2.) server.conf
        if not cmd:
            cmd = self.conf().get("start_command")

        # 3.) fallback
        if not cmd:
            cmd = self.default_start_cmd()

        cmd = cmd.format(
            server_exe = shlex.quote(self.exe_path()),
            server_dir = shlex.quote(self.directory())
        )
        return cmd

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

    def log_error_re(self):
        """
        **ABSTRACT**

        Returns a regex, that matches every line with a *severe* (critical)
        error.
        A severe error means, that the server does not run correct and needs
        to be restarted.
        """
        raise NotImplementedError()

    def world_address(self, world):
        """
        **ABSTRACT**

        Returns the address (ip, port) which is binded by the world.
        (None, None) should be returned, if the binding can not be retrieved.

        If the server is binded to all ip addresses, return the emtpy string
        ``""`` for the ip address.

        The port should be returned as integer. If it can not be retrieved,
        return None.
        """
        raise NotImplementedError()


# Vanilla
# '''''''

class VanillaBase(BaseServerWrapper):
    """
    Base class for all vanilla server versions.
    """

    def exe_path(self):
        return os.path.join(self.directory(), self.name())

    def default_start_cmd(self):
        return "java -jar {} nogui".format(shlex.quote(self.exe_path()))

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
            shutil.move(tmp_path, self.exe_path())
        return None

    def world_address(self, world):
        """
        """
        # Read the server.properties file in the world's directory.
        conf_path = os.path.join(world.directory(), "server.properties")
        try:
            with open(conf_path, "r") as file:
                conf = file.read()
        except (OSError, IOError) as err:
            port = None
            ip = None
        else:
            # Retrieve the values for *server-port* and *server-ip*.
            # Note, that we use the '^' and '$' chars, so that we only match
            # valid lines. If there is a syntax error in the configuration,
            # we will ignore the value and return None instead.
            port_re = "^server-port\s*=\s*([\d]{1,5})\s*$"
            port = re.findall(port_re, conf, re.MULTILINE)
            port = int(port[0]) if port else None

            ip_re = "^server-ip\s*=\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*$"
            ip = re.findall(ip_re, conf, re.MULTILINE)
            ip = ip[0] if ip else "localhost"
        return (ip, port)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


class Vanilla_1_8(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.8"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.8.9/minecraft_server.1.8.9.jar"

    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.8.*")

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


class Vanilla_1_9(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.9"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.9/minecraft_server.1.9.jar"

    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.9.*")

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)

class Vanilla_1_10(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.10"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.10.2/minecraft_server.1.10.2.jar"

    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.10.*")

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)

class Vanilla_1_11(VanillaBase):

    @classmethod
    def name(self):
        return "vanilla 1.11"

    def default_url(self):
        return "https://s3.amazonaws.com/Minecraft.Download/versions/1.11.2/minecraft_server.1.11.2.jar"

    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version 1\.11.*")

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)


# MinecraftForge
# ''''''''''''''


class MinecraftForgeBase(BaseServerWrapper):
    """
    Base class for the minecraft forge server.

    Todo:
        * check if :meth:`log_error_re` is correct implemented.
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

                # Clear the server directory.
                shutil.rmtree(self.directory())
                if not os.path.exists(self.directory()):
                    os.makedirs(self.directory())

                os.chdir(self.directory())
                if not os.path.samefile(self.directory(), os.curdir):
                    msg = "Could not chdir to {}".format(self.directory())
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
            if os.path.exists(self.directory()):
                shutil.rmtree(self.directory())

            raise
        return None

    def default_start_cmd(self):
        start_cmd = "java -jar {} nogui".format(shlex.quote(self.exe_path()))
        return start_cmd


class MinecraftForge_1_6(MinecraftForgeBase, Vanilla_1_6):

    @classmethod
    def name(self):
        return "minecraft forge 1.6"

    def default_url(self):
        return "http://files.minecraftforge.net/minecraftforge/minecraftforge-installer-1.6.4-9.11.1.916.jar"

    def exe_path(self):
        filenames = [filename \
                     for filename in os.listdir(self.directory()) \
                     if re.match("^minecraftforge-universal-1\.6.*.jar$", filename)]
        filename = filenames[0]
        return os.path.join(self.directory(), filename)


class MinecraftForge_1_7(MinecraftForgeBase, Vanilla_1_7):

    @classmethod
    def name(self):
        return "minecraft forge 1.7"

    def default_url(self):
        return "http://files.minecraftforge.net/maven/net/minecraftforge/forge/1.7.10-10.13.4.1614-1.7.10/forge-1.7.10-10.13.4.1614-1.7.10-installer.jar"

    def exe_path(self):
        filenames = [filename \
                     for filename in os.listdir(self.directory()) \
                     if re.match("^forge-1\.7.*.jar$", filename)]
        filename = filenames[0]
        return os.path.join(self.directory(), filename)


class MinecraftForge_1_8(MinecraftForgeBase, Vanilla_1_8):

    @classmethod
    def name(self):
        return "minecraft forge 1.8"

    def default_url(self):
        return "http://files.minecraftforge.net/maven/net/minecraftforge/forge/1.8.9-11.15.1.1722/forge-1.8.9-11.15.1.1722-installer.jar"

    def exe_path(self):
        filenames = [filename \
                     for filename in os.listdir(self.directory()) \
                     if re.match("^forge-1\.8.*.jar$", filename)]
        filename = filenames[0]
        return os.path.join(self.directory(), filename)


class MinecraftForge_1_10(MinecraftForgeBase, Vanilla_1_10):

    @classmethod
    def name(self):
        return "minecraft forge 1.10"

    def default_url(self):
        return "http://files.minecraftforge.net/maven/net/minecraftforge/forge/1.10.2-12.18.0.2008/forge-1.10.2-12.18.0.2008-installer.jar"

    def exe_path(self):
        filenames = [filename \
                     for filename in os.listdir(self.directory()) \
                     if re.match("^forge-1\.10.*.jar$", filename)]
        filename = filenames[0]
        return os.path.join(self.directory(), filename)


# Bungeecord
# ''''''''''

class BungeeCordServerWrapper(BaseServerWrapper):
    """
    Wraps only the **latest** BungeeCord version.

    Unfortunetly, the BungeeCord server uses the git commit hash value
    as its version number. So it would be too much work to keep track of the
    versions.
    """

    @classmethod
    def name(self):
        return "bungeecord"

    def default_url(self):
        return "http://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar"

    def exe_path(self):
        return os.path.join(self.directory(), self.name())

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
            shutil.move(tmp_path, self.exe_path())
        return None

    def default_start_cmd(self):
        return "java -jar {}".format(shlex.quote(self.exe_path()))

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

    def log_error_re(self):
        return re.compile(".* \[SEVERE\] .*", re.MULTILINE)

    def world_address(self, world):
        """
        """
        # Try to read and parse the configuration.
        # Note that it may not exist, not readable or parseable.
        conf_path = os.path.join(world.directory(), "config.yml")
        try:
            with open(conf_path) as file:
                conf = yaml.load(file)
        except (OSError, IOError) as err:
            ip, port = (None, None)
        else:
            # Try to extract the ip and port.
            try:
                adr = conf["listeners"][0]["host"]
                ip, port = adr.split(":")
            except:
                ip, port = (None, None)
            else:
                # Check if the ip address is valid.
                ip = ip.strip()
                if not re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
                    ip = None

                # Check if the server is bounded to all available ip addresses.
                if ip == "0.0.0.0":
                    ip = "localhost"

                # Check if the port is valid and convert it to an int.
                port = port.strip()
                port = int(port) if re.match("^\d{1,5}$", port) else None
        return (ip, port)


# Spigot (1.8+)
# '''''''''''''

class Spigot(BaseServerWrapper):
    """
    Wraps the **latest** Spigot version.
    """

    @classmethod
    def name(self):
        return "spigot latest"

    def default_url(self):
        return "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar"

    def build_dir(self):
        """
        You can specify a build directory in the :file:`server.conf`. If not
        specified, we will use a temporary directory:

        .. code-block:: ini

            [spigot latest]
            build_dir = /path/to/my/build/dir
        """
        if "build_dir" in self.conf():
            tmp = self.conf().get("build_dir")
            tmp = os.path.expanduser(tmp)
            tmp = os.path.abspath(tmp)
            return tmp
        return tempfile.mkdtemp(prefix='spigotmc')

    def install(self):
        if self.is_installed():
            return None

        # Download and build in /tmp
        build_dir = self.build_dir()

        log.info("Installing spigot ...")
        log.info("- Building in '{}' ...".format(build_dir))
        try:
            # Download the build tools.
            try:
                buildtools, http_resp = urllib.request.urlretrieve(
                    self.url(), os.path.join(build_dir, "BuildTools.jar")
                    )
            except Exception as err:
                raise ServerInstallationFailure(self, err)

            log.info("- BuildTools: '{}' ...".format(buildtools))

            # Run the BuildTools.jar file.
            with subprocess.Popen(
                ["java", "-jar", buildtools],
                cwd = build_dir,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            ) as proc:
                # Store the output of the installer in the logfiles.
                out, err = proc.communicate()
                out = out.decode()
                err = err.decode()
                log.info(out)
                log.error(err)

                # Check, if the installer exited with return code 0 and
                # throw an exception if not.
                if proc.returncode:
                    msg = "Installer returned with '{}'."\
                          .format(proc.returncode)
                    raise ServerInstallationFailure(self, msg)

            # Move the built files to *exe_path()*.
            jarfiles = glob.glob(
                os.path.join(build_dir, "Spigot/Spigot-Server/target/spigot-*.jar")
                )
            if len(jarfiles) > 0:
                jarfile = jarfiles[0]
                shutil.move(jarfile, self.exe_path())
            else:
                msg = "Could not find built spigot-*.jar file."
                raise ServerInstallationFailure(self, msg)

        finally:
            # Remove the build directory, if it's only a temporary dir.
            if "build_dir" not in self.conf():
                log.info("- Removing build directory {}".format(build_dir))
                shutil.rmtree(build_dir)
        return None

    def exe_path(self):
        return os.path.join(self.directory(), self.name())

    def default_start_cmd(self):
        return "java -jar {}".format(shlex.quote(self.exe_path()))

    def log_path(self):
        return "./logs/latest.log"

    def log_start_re(self):
        return re.compile("^.*Starting minecraft server version .*")

    def log_error_re(self):
        """
        Todo: Check if this regex is correct and matches an error line.
        """
        return re.compile(".*/SEVERE\].*", re.MULTILINE)

    def translate_command(self, cmd):
        return cmd

    def world_address(self, world):
        """
        """
        # Read the server.properties file in the world's directory.
        conf_path = os.path.join(world.directory(), "server.properties")
        try:
            with open(conf_path, "r") as file:
                conf = file.read()
        except (OSError, IOError) as err:
            port = None
            ip = None
        else:
            # Retrieve the values for *server-port* and *server-ip*.
            # Note, that we use the '^' and '$' chars, so that we only match
            # valid lines. If there is a syntax error in the configuration,
            # we will ignore the value and return None instead.
            port_re = "^server-port\s*=\s*([\d]{1,5})\s*$"
            port = re.findall(port_re, conf, re.MULTILINE)
            port = int(port[0]) if port else None

            ip_re = "^server-ip\s*=\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*$"
            ip = re.findall(ip_re, conf, re.MULTILINE)
            ip = ip[0] if ip else "localhost"
        return (ip, port)


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
            Vanilla_1_9,
            Vanilla_1_10,
            Vanilla_1_11,
            MinecraftForge_1_6,
            MinecraftForge_1_7,
            MinecraftForge_1_8,
            MinecraftForge_1_10,
            BungeeCordServerWrapper,
            Spigot,
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
