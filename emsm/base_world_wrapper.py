#!/usr/bin/env python3


"""
This module is independent from the application and
can be used to run and control a single world.
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
           "BaseWorldWrapper"
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
        filename = self.worldpath_to_ospath("server.log")

        try:
            with open(filename) as log:
                for line in log:
                    if "STARTING" in line.upper():
                        last_log = str()
                    last_log += line
        except FileNotFoundError:
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
        # XXX: screen -ls always exists with the exit code
        #   1, so it's convenient to use gestatusoutput.
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
    
    def send_command_get_output(self, server_cmd, timeout=10):
        """
        Like self.send_commmand(..) but waits timeout seconds for
        the echo in the logfiles and returns it.
        
        Raises: WorldIsOfflineError
        Raises: WorldCommandTimeout
        """
        filename = self.worldpath_to_ospath("server.log")

        # Save the current logfile size to parse the log
        # faster.
        with open(filename) as log:
            log.seek(0, 2)
            offset = log.tell()

        self.send_command(server_cmd)

        # Parse the logfile for a change.
        start_time = time.time()
        output = str()
        while (not output) and time.time() - start_time < timeout:
            time.sleep(0.2)
            
            with open(filename) as log:
                log.seek(offset, 0)
                output = log.read()
            
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
                # It's not the terminal of the user.
                if error.returncode == 256:
                    sys_cmd = "script -c {} /dev/null"\
                              .format(shlex.quote(sys_cmd))
                    subprocess.check_call(
                        shlex.split(sys_cmd), stdin=sys.stdin,
                        stdout=sys.stdout, stderr=sys.stderr)
                else:
                    raise
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
            time.sleep(0.2)
        
        # Delete the directory
        directory = self.worldpath_to_ospath("")
        
        try:
            shutil.rmtree(directory, ignore_errors=True)
        # XXX: Fixes an error with sudo / su
        except FileExistsError:
            pass
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
            os.chdir(old_wd)
                       
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

    def stop(self, message=str(), delay=5, timeout=5, force_stop=False):
        """
        Sends the message to the server and waits delay seconds before
        sending the stop command. If the server is still alive after
        timeout seconds, a WorldStopFailed exception will be raised.
        If force_stop is true, kill_processes will be called before
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
            time.sleep(0.05)
            
        if force_stop:
            self.kill_processes()
            
        if self.is_online():
            raise WorldStopFailed(self)
        return None
