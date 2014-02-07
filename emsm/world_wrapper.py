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

"""
The BaseWorldWrapper class is independent from the EMSM and can be
used to implement your own server wrapper, if you don't like EMSM.
"""


# Modules
# ------------------------------------------------
import time
import shutil
import os
import sys
import subprocess
import shlex
import signal
import collections


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
__all__ = ["WorldError", "WorldStatusError",
           "WorldIsOnlineError", "WorldIsOfflineError",
           "WorldStartFailed", "WorldStopFailed",
           "WorldCommandTimeout",           
           "BaseWorldWrapper", "WorldWrapper",
           "WorldManager"
           ]

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
    Raised, if an action can not be done because of the
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
        temp = temp.format(self.world.name)
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
               .format(self.world.name)
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
               .format(self.world.name)
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
               .format(self.world.name)
        return temp

    
# Classes
# ------------------------------------------------
class BaseWorldWrapper(object):
    """
    Provides methods to handle a minecraft world like
    start, stop, force-stop, ...
    """
    
    # Screen prefix for the minecraft-server sessions.
    # DO NOT CHANGE THIS VALUE IF A WORLD IS ONLINE!
    SCREEN_PREFIX = "minecraft_"
    
    def __init__(self, name, directory, auto_install=True):
        """
        If auto_install is true, the directory of the world will
        be created if it does not exist.
        """
        self.name = str(name)
        self.screen_name = self.SCREEN_PREFIX + self.name
        self.directory = directory

        if auto_install:
            self.install()
        return None
    
    # common
    # --------------------------------------------
    
    def worldpath_to_ospath(self, rel_path):
        """
        Converts the rel_path, that is relative to the root
        directory of the minecraft world, into the absolute
        path of the operating system.
        """
        return os.path.join(self.directory, rel_path)

    @property
    def log_path(self):
        """Returns the path to the log file of the world."""
        # MC 1.7+
        filename = self.worldpath_to_ospath("logs/latest.log")
        if os.path.exists(filename):
            return filename
        # Previous versions
        return self.worldpath_to_ospath("server.log")

    # server.properties
    # --------------------------------------------
    
    def get_properties(self):
        """
        Returns a dictionary with the properties.
        """
        filename = self.worldpath_to_ospath("server.properties")        

        # I'm using an OrderedDict to remain the order of
        # the properties.
        if not os.path.exists(filename):
            return collections.OrderedDict()
        
        properties = collections.OrderedDict()
        with open(filename) as file:
            for line in file:
                line = line.split("=")
                if len(line) != 2:
                    continue
                key = line[0].strip()
                val = line[1].strip()
                properties[key] = val
        return properties
    
    def overwrite_properties(self, **kwargs):
        """
        Overwrites the properties file to use the values of the
        keyword arguments.
        E.g.:
        self.overwrite_properties(motd="Hello world!")
        """
        filename = self.worldpath_to_ospath("server.properties") 

        properties = self.get_properties()
        properties.update(kwargs)

        properties = ["{}={}".format(key, val) \
                      for key, val in properties.items()]
        properties = "\n".join(properties)
        
        with open(filename, "w") as file:
            file.write(properties)
        return None
    
    # server.log
    # --------------------------------------------
    
    def get_log(self):
        """
        Returns the log of the world since the last start. If the
        logfile does not exist, an empty string will be returned.
        """         
        try:
            last_log = str()
            with open(self.log_path) as log:
                for line in log:
                    if "STARTING" in line.upper():
                        last_log = str()
                    last_log += line
        except (FileNotFoundError, IOError) as err:
            return str()
        return last_log

    # screen
    # --------------------------------------------
    
    def get_pids(self):
        """
        Returns a list with the pids of the screen sessions named
        self.screen_name
        """
        # Get sessions
        # XXX: screen -ls seems to exit always the exit code 1
        #   so it's convenient to use gestatusoutput.
        status, output = subprocess.getstatusoutput("screen -ls")
    
        # foo@bar:~$ screen -ls
        # There is a screen on:
        #         20405.minecraft_barz    (07/08/13 14:42:15)     (Detached)
        # 1 Socket in /var/run/screen/S-foo.
        
        # Filter PIDs
        pids = list()
        for line in output.split("\n"):
            if self.screen_name not in line:
                continue
            pid = line[:line.find(self.screen_name) - 1]
            pid = pid.strip()
            pid = int(pid)
            pids.append(pid)
        return pids
    
    def is_online(self):
        return bool(self.get_pids())

    def is_offline(self):
        return not self.is_online()

    def send_command(self, server_cmd):
        """
        Sends the given command to all screen sessions with
        the world's screen name.

        Raises: WorldIsOfflineError
        """
        if not self.is_online():
            raise WorldIsOfflineError(self)
        
        server_cmd += "\n"
        server_cmd = shlex.quote(server_cmd)
            
        pids = self.get_pids()
        for pid in pids:
            sys_cmd = "screen -S {0}.{1} -p 0 -X stuff {2}"\
                      .format(pid, self.screen_name, server_cmd)
            subprocess.call(shlex.split(sys_cmd))
        return None
    
    def send_command_get_output(self, server_cmd, timeout=10,
                                poll_intervall=0.2):
        """
        Like self.send_commmand(..) but checks every *poll_intervall*
        seconds, if content has been added to the logfile and returns the
        change. If no change could be detected after *timeout* seconds,
        an error will be raised.
        
        Raises: WorldIsOfflineError
        Raises: WorldCommandTimeout
        """
        filename = self.log_path

        # Save the current logfile size to parse the log faster.
        try:
            with open(filename) as log:
                log.seek(0, 2)
                offset = log.tell()
        except (FileNotFoundError, IOError):
            offset = 0

        self.send_command(server_cmd)

        # Parse the logfile for a change.
        start_time = time.time()
        output = str()
        while (not output) and time.time() - start_time < timeout:
            time.sleep(poll_intervall)

            try:           
                with open(filename) as log:
                    log.seek(offset, 0)
                    output = log.read()
            except (FileNotFoundError, IOError):
                break
            
        if not output:
            raise WorldCommandTimeout(self)
        return output

    def open_console(self):
        """
        Opens all screen sessions that match a pid in
        self.get_pids().

        Raises: WorldIsOfflineError
        """
        if not self.is_online():
            raise WorldIsOfflineError(self)
        
        pids = self.get_pids()
        for pid in pids:
            sys_cmd = "screen -x {pid}".format(pid=pid)

            try:
                subprocess.check_call(shlex.split(sys_cmd))
            except subprocess.CalledProcessError as error:
                # It's probably not the terminal of the user,
                # so try this one.
                sys_cmd = "script -c {} /dev/null"\
                          .format(shlex.quote(sys_cmd))
                subprocess.check_call(
                    shlex.split(sys_cmd), stdin=sys.stdin,
                    stdout=sys.stdout, stderr=sys.stderr)
        return None
    
    # setup
    # --------------------------------------------
    
    def install(self):
        """
        Creates the directory of the world.
        """   
        directory = self.worldpath_to_ospath("")  
        try:
            os.makedirs(directory, exist_ok=True)
        # XXX: Fixes an error with sudo / su
        except FileExistsError:
            pass
        return None

    def uninstall(self):
        """
        Uninstall

        Calls: self.kill_processes()
        """
        if self.is_online():
            self.kill_processes()
            
        # Delete the directory
        directory = self.worldpath_to_ospath("")

        # Try 5 times to remove the directory. This is necessairy, if the
        # world was online. *server.log.lck* made problems.
        for i in range(5):
            try:
                shutil.rmtree(directory)
            except FileExistsError:
                time.sleep(0.5)
            else:
                break
        return None
    
    # start / stop
    # --------------------------------------------------
    
    def start(self, server_start_cmd, init_properties=dict()):
        """
        Starts the world if the world is offline.

        Raises: WorldIsOnlineError
        Raises: WorldStartFailed
        """
        global _SCREEN
        
        if self.is_online():
            raise WorldIsOnlineError(self)
        
        self.overwrite_properties(**init_properties)

        # We need to change the cwd to the world's directory
        # to before starting the server.
        old_wd = os.getcwd()
        os.chdir(self.directory)
        try:
            if os.path.samefile(os.getcwd(), self.directory):
                sys_cmd = "{screen} -dmS {screen_name} {start_cmd}".format(
                    screen=_SCREEN, screen_name = self.screen_name,
                    start_cmd = server_start_cmd)
                subprocess.call(shlex.split(sys_cmd))
        finally:
            # We may have not the rights to change back.
            try:
                os.chdir(old_wd)
            except OSError:
                pass
                       
        if not self.is_online():
            raise WorldStartFailed(self)
        return None
    
    def kill_processes(self):
        """
        Kills the processes with the pid in self.get_pids()

        Raises: WorldStopFailed
        """
        pids = self.get_pids()
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

        if self.is_online():
            raise WorldStopFailed(self)
        return None        

    def stop(self, message=str(), delay=5, timeout=5, force_stop=False,
             poll_intervall=0.1):
        """
        Sends the *message* to the server and waits *delay* seconds before
        sending the stop command. Every *poll_intervall* seconds will be
        checked if the server is offline. If the server is still alive after
        *timeout* seconds, a WorldStopFailed exception will be raised.
        If *force_stop* is true, kill_processes will be called before
        raising a WorldStopFailed exception.
        
        Raises: WorldIsOfflineError
        Raises: WorldStopFailed
        """
        if self.is_offline():
            raise WorldIsOfflineError(self)

        for line in message.split("\n"):
            line = line.strip()
            self.send_command("say {}".format(line))

        self.send_command("save-all")
        time.sleep(delay)
        
        self.send_command("stop")
        start_time = time.time()
        while self.is_online() and time.time() - start_time < timeout:
            time.sleep(poll_intervall)
            
        if force_stop:
            self.kill_processes()
            
        if self.is_online():
            raise WorldStopFailed(self)
        return None


class WorldWrapper(BaseWorldWrapper):
    """
    This world wrapper uses the world configuration to get the
    values for parameters in some methods.

    Events:
        event                           parameter
        --------------------------------------------------------------
        world_uninstalled            -> world
        world_upcoming_status_change -> world, prev_status, end_status
        world_status_change          -> world, prev_status, end_status
        world_status_change_failure  -> world, prev_status, end_status
    """

    def __init__(self, app, name):
        """
        application is a reference to the running application.
        """
        self._app = app
        self.conf = app.conf.worlds[name]
        self.server = app.server.get(self.conf["server"])

        # Events
        self.on_uninstall = app.events.get_event(
            "world_uninstalled")
        self.on_upcoming_status_change = app.events.get_event(
            "world_upcoming_status_change")
        self.on_status_change = app.events.get_event(
            "world_status_change")
        self.on_status_change_failure = app.events.get_event(
            "world_status_change_failure")

        BaseWorldWrapper.__init__(
            self, name, app.paths.get_world_dir(name))
        return None

    # setup
    # --------------------------------------------

    def uninstall(self):
        """
        Removes the world's directory and the configuration of the world.
        When done, emits the "world_uninstalled" signal.
        """
        BaseWorldWrapper.uninstall(self)
        self._app.conf.worlds.remove_section(self.name)
        self.on_uninstall.emit(self)
        return None

    # start / stop
    # --------------------------------------------

    def _perform_status_change(self, func, end_status):
        """
        Emit *world_upcoming_status_change* before executing any command, that
        could cause a status change.
        If the status change is successful, *world_status_change* is emitted,
        else *world_status_change_failed*.

        *func* requires no arguments and should change the statuus of this
        world.
        """
        prev_status = self.is_online()
        self.on_upcoming_status_change.emit(self, prev_status, end_status)
        try:
            func()
        except WorldError as error:
            self.on_status_change_failure.emit(self, prev_status, end_status)
            raise
        else:
            self.on_status_change(self, prev_status, end_status)
        return None

    def start(self):
        """
        Starts the world.
        """
        start_cmd = self.server.get_start_cmd(
            int(self.conf["min_ram"]), int(self.conf["max_ram"]))
        # We need to overwrite the port each start, so that only EMSM controls
        # the port and makes sure, that everything is in sync.
        init_properties = {"server-port": self.conf["port"]}

        func = lambda: BaseWorldWrapper.start(self, start_cmd, init_properties)
        self._perform_status_change(func, True)
        return None

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
        func = lambda: BaseWorldWrapper.stop(
            self, self.conf["stop_message"], int(self.conf["stop_delay"]),
            int(self.conf["stop_timeout"]), force_stop)
        return self._perform_status_change(func, False)


class WorldManager(object):
    """
    Works as a container for the WorldWrapper instances.
    """

    def __init__(self, app):
        self._app = app

        # Maps the name of the world to the world wrapper
        # world.name => world
        self._worlds = dict()

        self._app.events.connect(
            "world_uninstalled", self._remove, create=True)
        return None

    def load(self):
        """
        Loads all worlds declared in the configuration file.
        """
        conf = self._app.conf.worlds
        for section in conf.sections():
            world = WorldWrapper(self._app, section)
            self._worlds[world.name] = world
        return None

    # container
    # --------------------------------------------

    def _remove(self, world):
        if world in self._worlds:
            del self._worlds[world.name]
        return None

    def get(self, worldname):
        return self._worlds[worldname]

    def get_all(self):
        return list(self._worlds.values())

    def get_by_pred(self, func=None):
        """
        Returns the worlds where func returns true.
        E.g.:
        func = lambda w: w.is_running()
        """
        return list(filter(func, self._worlds.values()))

    def get_selected(self):
        """
        Returns all worlds that have been selected per command line argument.
        """
        args = self._app.argparser.args
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
