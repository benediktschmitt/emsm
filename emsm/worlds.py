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

#std
import time
import shutil
import os
import sys
import subprocess
import shlex
import signal
import collections
import re
import random
import socket
import logging

# third party
import blinker


# Backward compatibility
# ------------------------------------------------

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

if not hasattr(shlex, "which"):
    shlex.which = lambda s: s

if not hasattr(subprocess, "DEVNULL"):
    subprocess.DEVNULL = os.open(os.devnull, os.O_RDWR)

try:
    FileNotFoundError
    FileExistsError
except NameError:
    FileNotFoundError = OSError
    FileExistsError = OSError

    
# Data
# ------------------------------------------------

__all__ = [
    "WorldError",
    "WorldStatusError",
    "WorldIsOnlineError",
    "WorldIsOfflineError",
    "WorldStartFailed",
    "WorldStopFailed",
    "WorldCommandTimeout",
    "WorldWrapper",
    "WorldManager"
    ]

log = logging.getLogger(__file__)

_SCREEN = shlex.which("screen")


# Exceptions
# ------------------------------------------------

class WorldError(Exception):
    """
    Base class for all other exceptions in this module.
    """
    pass


class WorldStatusError(WorldError):    
    """
    Raised, if a task can not be done because of the
    current status of the world (online or not online).
    """
    
    def __init__(self, world, is_online):
        self.world = world
        self.is_online = is_online
        return None
    
    def __str__(self):
        if self.is_online:
            temp = "The world '{}' is online!"
        else:
            temp = "The world '{}' is offline!"
        temp = temp.format(self.world.name())
        return temp

    
class WorldIsOnlineError(WorldStatusError):
    """
    Raised if a world is online but should be offline.
    """
    
    def __init__(self, world):
        WorldStatusError.__init__(self, world, True)
        return None

    
class WorldIsOfflineError(WorldStatusError):
    """
    Raised if a world is offline but should be online.
    """
    
    def __init__(self, world):
        WorldStatusError.__init__(self, world, False)
        return None

    
class WorldStartFailed(WorldError):    
    """
    Raised if the world start failed.
    """
    
    def __init__(self, world):
        self.world = world
        return None
    
    def __str__(self):
        temp = "The start of the world '{}' failed!"\
               .format(self.world.name())
        return temp

    
class WorldStopFailed(WorldError):    
    """
    Raised if the world stop failed.
    """
    
    def __init__(self, world):
        self.world = world
        return None
    
    def __str__(self):
        temp = "The stop of the world '{}' failed!"\
               .format(self.world.name())
        return temp

    
class WorldCommandTimeout(WorldError):    
    """
    Raised, when the server did not react in x seconds.
    """
    
    def __init__(self, world = ""):
        self.world = world
        return None
    
    def __str__(self):
        temp = "The world '{}' did not react!"\
               .format(self.world.name())
        return temp


# Functions
# ------------------------------------------------

_FOUND_PORTS = list()
def get_unused_port(min_port=10000, max_port=65535, interface=""):
    """
    Returns an unused port in the intervall *[min_, max_]* on the
    *interface*.
    """
    global _FOUND_PORTS
    
    if max_port > 65535:
        raise ValueError("max_port has to be less than 65535") 
    if min_port < 0:
        raise ValueError("min_port has to be greater or equal to 0")

    while True:
        port = random.randint(min_port, max_port)
        if port in _FOUND_PORTS:
            continue
        
        # Check the port.
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
            try:
                s.bind((interface, port))
            except OSError as error:
                pass
            else:
                _FOUND_PORTS.append(port)
                return port
    return None


# Classes
# ------------------------------------------------

class WorldWrapper(object):
    """
    Provides methods to handle a minecraft world like
    :meth:`start`, :meth:`stop`, :meth:`restart`, ...

    The WorldWrapper is initialised using the configuration options in the
    section with the name *name* in the :file:`server.conf` configuration
    file.
    """
    
    # Screen prefix for the minecraft-server sessions.
    # DO NOT CHANGE THIS VALUE IF A WORLD IS ONLINE!
    _SCREEN_PREFIX = "minecraft_"

    #: Signal, that is emitted when a world has been uninstalled.
    world_uninstalled = blinker.signal("world_uninstalled")

    #: Signal, that is emitted when a world is about to start.
    world_about_to_start = blinker.signal("world_about_to_start")

    #: Signal, that is emitted when a world has been started.
    world_started = blinker.signal("world_started")

    #: Signal, that is emitted when a world could not be started.
    world_start_failed = blinker.signal("world_start_failed")

    #: Signal, that is emitted when a world is about to be stopped.
    world_about_to_stop = blinker.signal("world_about_to_stop")

    #: Signal, that is emitted when a world has been stopped.
    world_stopped = blinker.signal("world_stopped")

    #: Signal, that is emitted when a world could not be stopped.
    world_stop_failed = blinker.signal("world_stop_failed")
    
        
    def __init__(self, app, name):
        """
        """
        log.info("initialising world '{}' ...".format(name))
        
        self._app = app
        self._conf = app.conf().worlds()[name]
        self._check_conf()

        # The ServerWrapper for the server that powers this world.
        self._server = app.server().get(self._conf["server"])

        # The name of the world.
        self._name = name

        # The directory that contains the world data.
        self._directory = app.paths().world_dir(name)
        return None

    def _check_conf(self):
        """
        Checks if the configuration contains only valid values and
        types (float, int, ...).

        :raises ValueError:
            If a configration option has an invalid value.
        :raises TypeError:
            If a configuration option has an invalid type.
        """
        # port
        if self._conf["port"] == "<auto>":
            self._conf["port"] = str(get_unused_port())

        if not self._conf["port"].isdecimal():
            raise TypeError("conf:port is not an integer")
        if not 0 <= int(self._conf["port"]) <= 65535:
            raise ValueError("conf:port is not in range [0, 65535]")

        # stop timeout
        if not self._conf["stop_timeout"].isdecimal():
            raise TypeError("conf:stop_timeout is not an integer")

        # stop delay
        if not self._conf["stop_delay"].isdecimal():
            raise TypeError("conf:stop_delay is not an integer")

        # server
        if not self._conf["server"] in self._app.server().get_names():
            raise ValueError("conf:server does not exist")
        return None

    def worldpath_to_ospath(self, rel_path):
        """
        Converts *rel_path*, that is relative to the root directory of the
        minecraft world, into the absolute path of the operating system.

        **Example:**

        .. code-block:: python
        
            >>> # I assume the EMSM root is: "/home/minecraft"
            >>> foo.name()
            "foo"
            >>> foo.worldpath_to_ospath("server.properties")
            "/opt/minecraft/worlds/foo/server.properties"
            
        .. seealso::
        
            * :meth:`directory`
        """
        return os.path.join(self._directory, rel_path)
    
    def conf(self):
        """
        The configuration section of this world.

        .. seealso::
        
            * :class:`~emsm.conf.WorldsConfiguration`
        """
        return self._conf

    def server(self):
        """
        The :class:`~emsm.server.ServerWrapper` for the server that runs
        this world.
        """
        return self._server

    def set_server(self, server):
        """
        Changes the server that runs this world. The world has to be offline.

        :param emsm.server.ServerWrapper server:
            The new server

        :raises WorldIsOnlineError*
            if the world is online.
        """
        if self.is_online():
            raise WorldIsOnlineError(self)

        # Break, if we have nothin to do.
        if server is self._server:
            return None

        self._server = server
        self._conf["server"] = server.name()

        log.info("assigned '{}' server to the world '{}'."\
                 .format(server.name(), self._name)
                 )
        return None

    def name(self):
        """
        The name of the world.

        This is the name of the configuration section in :file:`worlds.conf` and
        the folder name in the :file:`worlds` directory.
        """
        return self._name

    def screen_name(self):
        """
        Returns the name of the screen sessions that run the server of this
        world.
        """
        return WorldWrapper._SCREEN_PREFIX + self._name

    def directory(self):
        """
        Returns the directory that contains all world data generated by the
        minecraft server.

        If the world is run by the *mojang* minecraft server, this directory
        contains the :file:`server.properties`, :file:`whitelist.json`, ...
        files.
        """
        return self._directory

    def log_path(self):
        """
        Returns the path to the log file of the world.

        .. todo::
        
            Check if this value is also server dependant and move the
            functionlity of getting the correct log path to the server.
        """
        # MC 1.7+
        filename = self.worldpath_to_ospath("logs/latest.log")
        if os.path.exists(filename):
            return filename
        # Previous versions
        return self.worldpath_to_ospath("server.log")

    def latest_log(self):
        """
        Returns the log of the world since the last start. If the
        logfile does not exist, an empty string will be returned.

        .. todo::
        
            * The *start* keyword which signalises a server restart in the
              log is server independant and should be moved to the
              ServerWrapper features.
            * The whole *latest_log* thing should be moved to the ServerWrapper.
        """
        # Matches all lines in the log, that signalize the start of
        # a server.
        re_start_line = re.compile(".*(?:STARTING).*", re.IGNORECASE)
        
        try:
            last_log = str()
            with open(self.log_path()) as log:
                for line in log:
                    if re.match(re_start_line, line):
                        last_log = str()
                    last_log += line
        except (FileNotFoundError, IOError) as err:
            last_log = str()
        return last_log
    
    def server_properties(self):
        """
        Returns a dictionary with the content of the
        :file:`server.properties` file.
        """
        filename = self.worldpath_to_ospath("server.properties")

        # Use an OrderedDict to preserve the order.
        properties = collections.OrderedDict()
        try:
            with open(filename) as file:
                for line in file:
                    line = line.split("=")
                    if len(line) != 2:
                        continue
                    key = line[0].strip()
                    val = line[1].strip()
                    properties[key] = val
        except (FileNotFoundError, IOError):
            pass
        return properties
    
    def overwrite_properties(self, **kwargs):
        """
        Overwrites the :file:`server.properties` file with the values
        of the keyword arguments.

        **Example:**

        .. code-block:: python
        
            >>> world.overwrite_properties(motd="Hello world!")
            >>> world.overwrite_properties(port="42424")
            >>> world.overwrite_properties(motd="Hello world!", port="42424")

        .. todo::
        
            Rename this method to ``overwrite_server_properties``.
        """
        filename = self.worldpath_to_ospath("server.properties") 

        properties = self.server_properties()
        properties.update(kwargs)

        properties_str = "\n".join("{}={}".format(key, val) \
                                   for key, val in properties.items())
        
        with open(filename, "w") as file:
            file.write(properties_str)
        return None

    def address(self):
        """
        Returns the network address of the minecraft server, that runs
        this world.

        .. todo::
        
            This may be server dependant, so move it to the ServerWrapper
            class.
        """
        properties = self.server_properties()
        
        ip = properties.get("server-ip", "")
        port = properties.get("server-port", "")
        port = int(port) if port.isdigit() else 25565
        return (ip, port)

    
    def pids(self):
        """
        Returns a list with the pids of the screen sessions with the name
        :meth:`screen_name`.
        """
        # Get sessions
        # XXX: screen -ls seems to exit always with the exit code 1.
        #   so it's convenient to use gestatusoutput.
        status, output = subprocess.getstatusoutput("screen -ls")

        # Example output (without the '>' char):
        #
        # > foo@bar:~$ screen -ls
        # > There is a screen on:
        # >        20405.minecraft_barz    (07/08/13 14:42:15)     (Detached)
        # > 1 Socket in /var/run/screen/S-foo.
        
        # Filter the PIDs
        re_pid = re.compile(
            "^\s*(\d+?).{screen_name}".format(screen_name=self.screen_name()),
            re.MULTILINE
            )
        pids = re.findall(re_pid, output)
        pids = [int(pid) for pid in pids]
        return pids
    
    def is_online(self):
        """
        Returns ``True`` if the world is currently running.
        """
        return bool(self.pids())

    def is_offline(self):
        """
        Returns ``True`` if the world is currently **not** running.
        """
        return not self.is_online()

    def send_command(self, server_cmd):
        """
        Sends the given command to all screen sessions with the world's screen
        name.

        :raises WorldIsOfflineError:
            if the world is offline.

        .. warning::

            There is no guarantee, that the server reacted to the command.
        """
        pids = self.pids()

        # Break if the world is offline.
        if not pids:
            raise WorldIsOfflineError(self)

        # Quote the command.
        # The '\n' simulates pressing the ENTER key in the screen session.
        server_cmd += "\n\n"
        server_cmd = shlex.quote(server_cmd)

        # Send the command to the server.
        for pid in pids:
            sys_cmd = "screen -S {0}.{1} -p 0 -X stuff {2}"\
                      .format(pid, self.screen_name(), server_cmd)
            sys_cmd = shlex.split(sys_cmd)
            subprocess.call(sys_cmd)
        return None
    
    def send_command_get_output(self, server_cmd, timeout=10,
                                poll_intervall=0.2):
        """
        Like :meth:`send_commmand` but checks every *poll_intervall*
        seconds, if content has been added to the logfile and returns the
        change. If no change could be detected after *timeout* seconds,
        an error will be raised.

        :raises WorldIsOfflineError:
            if the world is offline.
        :raises WorldCommandTimeout:
            if the world did not react within *timeout* seconds.
        """
        # Save the current size of the logfile to detect changes.
        try:
            with open(self.log_path()) as log:
                log.seek(0, 2)
                offset = log.tell()
        except (FileNotFoundError, IOError):
            offset = 0

        # Send the command.
        self.send_command(server_cmd)

        # Parse the logfile for a change.
        start_time = time.time()
        output = str()
        while (not output) and time.time() - start_time < timeout:
            time.sleep(poll_intervall)

            try:           
                with open(self.log_path()) as log:
                    log.seek(offset, 0)
                    output = log.read()
            except (FileNotFoundError, IOError):
                break
        
        if not output:
            raise WorldCommandTimeout(self)
        return output

    def open_console(self):
        """
        Opens **all** screen sessions whichs pid is in :meth:`pids`.

        :raises WorldIsOfflineError:
            if the world is offline.
        """
        pids = self.pids()

        # Break if the world is offline.
        if not pids:
            raise WorldIsOfflineError(self)

        # Open all world screen sessions (one for each found pid).
        for pid in pids:
            sys_cmd = "screen -x {pid}".format(pid=pid)
            sys_cmd = shlex.split(sys_cmd)

            try:
                subprocess.check_call(sys_cmd)
            except subprocess.CalledProcessError as error:
                # It's probably not the terminal of the user,
                # so try this one.
                sys_cmd = "script -c {} /dev/null"\
                          .format(shlex.quote(sys_cmd))
                subprocess.check_call(
                    shlex.split(sys_cmd),
                    stdin = sys.stdin,
                    stdout = sys.stdout,
                    stderr = sys.stderr
                    )
        return None


    def is_installed(self):
        """
        Returns ``True`` if the :meth:`directory` of the world exists,
        otherwise ``False``.

        .. seealso::
        
            * :meth:`directory`
            * :meth:`install`
            * :meth:`uninstall`
        """
        return os.path.exists(self._directory) \
               and os.path.isdir(self._directory)
        
    def install(self):
        """
        Creates the directory of the world.

        .. seealso::
        
            * meth:`directory`
        """ 
        try:
            os.makedirs(self._directory, exist_ok=True)
        # XXX: Fixes an error with sudo / su
        except FileExistsError:
            pass
        return None

    def uninstall(self):
        """
        Stops the world and removes the world directory.

        .. seealso::
        
            * :meth:`kill_processes`
            * :meth:`directory`
        """
        self.kill_processes()

        # Try 5 times to remove the directory. This is necessairy, if the
        # world was online and fixes a problem with *server.log.lck*.
        for i in range(5):
            try:
                shutil.rmtree(self._directory)
            except FileExistsError:
                time.sleep(0.5)
            else:
                break

        # Remove the configuration.
        self._app.conf().worlds().remove_section(self._name)

        # Emit the corresponing signal to this event.
        WorldWrapper.world_uninstalled.send(self)
        return None

    
    def start(self, init_properties=None):
        """
        Starts the world if the world is offline. If the world is already
        online, nothing happens.

        **Signals:**
        
            * :attr:`world_about_to_start`
            * :attr:`world_started`
            * :attr:`world_start_failed`
            
        :raises WorldStartFailed:
            if the world could not be started.
        """
        global _SCREEN

        # Break if the world is already online.
        if self.is_online():
            return None

        WorldWrapper.world_about_to_start.send(self)

        # Overwrite the server.properties before we start.
        if init_properties is None:
            init_properties = dict()
        init_properties["server-port"] = self._conf["port"]
        self.overwrite_properties(**init_properties)

        # We need to change the current working directory to the world's
        # directory so that the server starts in the correct environment.
        old_wd = os.getcwd()
        os.chdir(self.directory())
        try:
            if os.path.samefile(os.getcwd(), self.directory()):
                sys_cmd = "{screen} -dmS {screen_name} {start_cmd}".format(
                    screen = _SCREEN,
                    screen_name = self.screen_name(),
                    start_cmd = self._server.start_cmd()
                    )
                sys_cmd = shlex.split(sys_cmd)
                subprocess.call(sys_cmd)
        finally:
            # We may have not the rights to change back.
            try:
                os.chdir(old_wd)
            except OSError:
                pass

        # Check if the world is really online.
        if not self.is_online():
            WorldWrapper.world_start_failed.send(self)
            raise WorldStartFailed(self)
        
        WorldWrapper.world_started.send(self)
        return None

    
    def kill_processes(self):
        """
        Kills all processes with a pid in :meth:`pids`.

        **Signals:**       
        
            * :attr:`world_about_to_stop`
            * :attr:`world_stopped`
            * :attr:`world_stop_failed`
            
        :raises WorldStopFailed: if the process could not be killed.
       
        .. seealso::
        
            * :meth:`pids`
        """
        pids = self.pids()
        
        # Break if the world is already offline.
        if not pids:
            return None

        # Kill all processes.
        WorldWrapper.world_about_to_stop.send(self)
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

        # Check if the world is now offline.
        if self.is_online():
            WorldWrapper.world_stop_failed.send(self)
            raise WorldStopFailed(self)

        WorldWrapper.world_stopped.send(self)
        return None
    

    def stop(self, force_stop=False, message=None, delay=None,
             timeout=None):
        """
        Stops the server.
        
        :param str message:
            Send to the world before the :meth:`stop` command is executed.
        :param float delay:
            Time in seconds that is waited between seding the *message*
            and executing the :meth`stop` command.
        :param float timeout:
            Maximum time in seconds waited for the server stop after
            executing the :meth:`stop` command.
        :param bool force_stop:
            If true and the server could not be stopped,
            :meth:`kill_processes` is called.

        **Signals:**
        
            * :attr:`world_about_to_stop`
            * :attr:`world_stopped`
            * :attr:`world_stop_failed`

        :raises WorldStopFailed: if the world coul not be stopped.

        .. seealso::

            * :meth:`kill_processes`
            * :meth:`is_offline`
        """
        # Break if the world is already offline.
        if self.is_offline():
            return None

        WorldWrapper.world_about_to_stop.send(self)

        # Get the default parameter values from the configuration.
        if message is None:
            message = self._conf["stop_message"]
        if delay is None:
            delay = int(self._conf["stop_delay"])
        if timeout is None:
            timeout = int(self._conf["stop_timeout"])

        # Send the stop_message.
        for line in message.split("\n"):
            line = line.strip()
            self.send_command("say {}".format(line))

        # Save the world and wait delay seconds to make sure the
        # world is saved and the stop_message can be read.
        self.send_command("save-all")
        time.sleep(delay)

        # Stop the world.
        self.send_command("stop")
        start_time = time.time()
        while self.is_online() and time.time() - start_time < timeout:
            time.sleep(0.25)

        # Force the stop if necessairy.
        if force_stop:
            self.kill_processes()

        # Check if the world is offline.
        if self.is_online():
            WorldWrapper.world_stop_failed.send(self)
            raise WorldStopFailed(self)

        WorldWrapper.world_stopped.send(self)
        return None

    def restart(self, force_restart=False, stop_args=None):
        """
        Restarts the server.

        :param bool force_restart:
            Forces the stop of the server by calling :meth:`kill_processes`` if
            necessairy.
        :param dict stop_args:
            If provided, these values are passed to :meth:`stop`.

        **Signals:**
        
            * :attr:`world_about_to_stop`
            * :attr:`world_stopped`
            * :attr:`world_stop_failed`            
            * :attr:`world_about_to_start`
            * :attr:`world_started`
            * :attr:`world_start_failed`

        :raises WorldStopFailed:
            if the world could not be stopped.
        :raises WorldStartFailed:
            if the world could not be restarted.
            
        .. seealso::
        
            * :meth:`stop`
            * :meth:`start`
        """
        if stop_args is None:
            stop_args = dict()
            
        self.stop(force_stop=force_restart, **stop_args)
        self.start()
        return None
    
    
class WorldManager(object):
    """
    Works as a container for the :class:`WorldWrapper` instances.
    """

    def __init__(self, app):
        self._app = app

        # Maps the name of the world to the world wrapper
        # world.name() => world
        self._worlds = dict()

        WorldWrapper.world_uninstalled.connect(self._remove)
        return None

    def load_worlds(self):
        """
        Loads all worlds declared in the :file:`worlds.conf` configuration
        file.

        .. seealso::
        
            * :class:`~emsm.conf.WorldsConfiguration`
        """
        conf = self._app.conf().worlds()
        for section in conf.sections():
            world = WorldWrapper(self._app, section)
            self._worlds[world.name()] = world

            # Make sure the folder exists.
            if not world.is_installed():
                world.install()
        return None

    # container
    # --------------------------------------------

    def _remove(self, world):
        """
        Removes the :class:`WorldWrapper` *world* from the internal map.
        """
        if world.name() in self._worlds:
            del self._worlds[world.name()]
        return None

    def get(self, worldname):
        """
        Returns the :class:`WorldWrapper` for the world with the name
        *worldname* or ``None`` if there is no world with that name.
        """
        return self._worlds.get(worldname)

    def get_all(self):
        """
        Returns a list with all loaded worlds.
        """
        return list(self._worlds.values())

    def get_by_pred(self, pred=None):
        """
        Filters the worlds using the predicate *pred*.

        **Example:**

        .. code-block:: python
        
            >>> # All running worlds
            >>> wm.get_by_pred(lambda w: w.is_online())
            ...

        .. seealso::
        
            * :meth:`get_all`
        """
        return list(filter(pred, self._worlds.values()))

    def get_selected(self):
        """
        Returns all worlds that have been selected per command line argument.

        .. seealso::

            * :meth:`emsm.argparse_.ArgumentParser.args`
        """
        args = self._app.argparser().args()
        
        selected_worlds = args.worlds
        all_worlds = args.all_worlds
        
        if all_worlds:
            return list(self._worlds.values())
        else:
            return [self._worlds[world] for world in selected_worlds]

    def get_names(self):
        """
        Returns a list with the names of all worlds.
        """
        return list(self._worlds.keys())
