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
About
-----

This plugin provides a user interface for the server wrapper. It handles
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

.. code-block:: ini

    [worlds]
    default_log_start = 0
    default_log_limit = 10
    open_console_delay = 1
    send_command_timeout = 10
   
**default_log_start**

    Is the first line of the log, that is printed. Can be overwritten by a
    command line argument.
   
**default_log_limit**

    Is the default number of log lines, that is printed at once. This
    value can be overwritten by a command line argument too.
   
**open_console_delay**

    Time between printing the WARNING and opening the console.

**send_command_timeout**

    Maximum time waited for the response of the minecraft server,
    if the ``--verbose-send`` command is used.
      
Arguments
---------

.. option:: --configuration
   
    Prints the section of the world in the :file:`worlds.conf`.

.. option:: --directory

    Prints the directory path that contains the world.
   
.. option:: --log

    Prints the log.
   
.. option:: --log-start LINE

    The first line of the log that is printed. If *'-10'* (with quotes!), the 
    10th last line will be the first line that is printed.
   
.. option:: --log-limit LINES

    Limits the number of printed lines.
   
.. option:: --pid

    Prints the PID of the screen session that runs the server.
   
.. option:: --status

    Prints the status of the world (online or offline).
   
.. option:: --send CMD

    Sends the command to the world.
   
    .. note:: Escaping commands with **spaces**
   
        If you want to send a command like ``say Hello players!``, you have to
        escape it.
      
        .. code-block:: bash
      
            minecraft -W worlds --send 'say Hello players!'
   
.. option:: --verbose-send CMD

    Sends the command to the server and prints the echo in the logfiles.
   
.. option:: --console

    Opens the server console.
   
.. option:: --start

    Starts the world
   
.. option:: --stop

    .. warning::
   
        Stopping the world not using the dedicated commands, will **not** 
        call the **event dispatcher** and may cause bugs.
      
    Stops the world
   
.. option:: --force-stop

   Like --stop, but kill the processes if the world is still online
   after the smooth stop.   
   
.. option:: --kill

    .. warning::

        Using this command can cause data loss.
      
    Kills the process of the world.
   
.. option:: --restart
   
    Restarts the world. If the world is offline, the world will be started.
   
.. option:: --force-restart

    Like --restart, but forces the stop of the world if necessairy.
   
.. option:: --uninstall

    Removes the world and its configuration.
   
Examples
---------

.. code-block:: bash
   
    # Start all worlds:
    $ minecraft -W worlds --start
   
    # Send a command to the server and print the console output:
    $ minecraft -W worlds --verbose-send list
    $ minecraft -W worlds --verbose-send '"say Use more TNT!"'
   
    # Print the log of the world *foo*:
    $ minecraft -w foo worlds --log
    $ minecraft -w foo worlds --log-start '"-20"'
    $ minecraft -w foo worlds --log-limit '"5"'
    $ minecraft -w foo worlds --log-start '"-50'" --log-limit 10
   
    # Open the console of a running world
    $ minecraft -w bar worlds --console
   
    ...
"""


# Modules
# --------------------------------------------------

# std
import os
import sys
import time

# emsm
import emsm
from emsm.base_plugin import BasePlugin


# Data
# --------------------------------------------------

PLUGIN = "Worlds"


# Classes
# --------------------------------------------------
class MyWorld(object):
    """
    Wraps an EMSM WorldWrapper instance. :)
    """    

    def __init__(self, app, world):
        """
        """
        self._app = app
        self._world = world
        return None

    def world(self):
        """
        Returns the wrapped WorldWrapper object.
        """
        return self._world

    def print_conf(self):
        """
        Prints the configuration of the world.

        See also:
            * WorldWrapper.conf()
        """
        conf = self._world.conf().items()
        
        print("{} - configuration:".format(self._world.name()))
        for key, value in sorted(conf):
            # Make sure, the indent of multiline values is correct.
            value = value.replace("\n", "\n\t\t")
            
            print("\t", key, "=", value)
        return None
    
    def print_directory(self):
        """
        Prints the path to the world's directory.

        See also:
            * WorldWrapper.directory()
        """        
        print("{} - directory:".format(self._world.name()))
        print("\t", self._world.directory())
        return None

    def print_latest_log(self, start_line=0, line_limit=20):
        """
        Prints the latest log of the world.

        Parameters:
            * start_line
                The number of the line that is printed first. If < 0, we start
                counting at the end.
            * line_limit
                The number of log lines that is printed. *0* means no limit.

        Example:
            >>> # Print the first 20 lines since the server start.
            >>> world.print_latest_log(0, 20)
            ...
            >>> # Print the latest 20 lines..
            >>> world.print_latest_log(-1, 20)
            >>> ...

        See also:
            * WorldWrapper.latest_log()
        """
        log = self._world.latest_log()
        log = log.split("\n")
        
        # Make sure that the limits are valid.
        # 0 <= start <= size
        # limit <= size - start
        num_lines = len(log)
        
        if start_line >= 0:
            start_line = min(start_line, num_lines)
        else:
            # start_line < 0
            start_line = max(0, num_lines + start_line)

        if line_limit != 0:
            line_limit = min(line_limit, num_lines - start_line)
            end_line = start_line + line_limit
        else:
            end_line = num_lines

        # Print the log section.
        print("{} - latest-log - line {}-{}/{}:"\
              .format(self._world.name(), start_line, end_line, num_lines))
        for line in range(start_line, end_line):
            print("\t", log[line])
        return None

    def print_pids(self):
        """
        Prints the pids of the screen sessions that run the minecraft server
        for this world.

        See also:
            * WorldWrapper.pids()
        """
        pids = self._world.pids()
        
        print("{} - pids:".format(self._world.name()))
        for pid in pids:
            print("\t", pid)
        return None

    def print_status(self, status=None):
        """
        Prints the current status (*offline* or *online*) of the world.

        See also:
            * WorldWrapper.is_online()
        """
        print("{} - status:".format(self._world.name()))
        if self._world.is_online():
            print("\t", "online")
        else:
            print("\t", "offline")
        return None

    def send_command(self, cmd):
        """
        Sends the command *cmd* to the server.

        Params:
            * cmd
                The minecraft server command to send.

        See also:
            * WorldWrapper.send_command()
        """
        try:
            self._world.send_command(cmd)
        except emsm.worlds.WorldIsOfflineError:
            print("{} - send-command:".format(self._world.name()))
            print("\t", "FAILURE: The world is offline.")
        else:
            print("{} - send-command:".format(self._world.name()))
            print("\t", "The command '{}' has been sent to the server.".format(cmd))
        return None
    
    def verbose_send_command(self, cmd, timeout):
        """
        Sends the command to the world and prints the output.

        Params:
            * cmd
                The minecraft command that is sent to the server.
            * timeout
                Maximum time waited for the server response.

        See also:
            * WorldWrapper.send_command_get_output()
        """
        try:
            output = self._world.send_command_get_output(
                server_cmd=cmd, timeout=timeout
                )
        except emsm.worlds.WorldIsOfflineError:
            print("{} - send-command:".format(self._world.name()))
            print("\t", "FAILURE: The world is offline.")
        except emsm.worlds.WorldCommandTimeout:
            print("{} - send-command:".format(self._world.name()))
            print("\t", "FAILURE: The world did not react.")
        else:
            print("{} - send-command:".format(self._world.name()))
            for line in output.split("\n"):
                print("\t", line)
        return None

    def open_console(self, delay=1):
        """
        Opens the screen session of the world's server process.

        Parameters:
            * delay
                The time between the warning message and the actual
                *open* command.

        See also:
            * WorldWrapper.open_console()
        """
        if self._world.is_online():
            print("{} - console:".format(self._world.name()))
            print("\t", "NOTE: Press [ctrl + a + d] to detach from the console.")
            print("\t", "WARNING: When you stop the server in the session, "\
                        "EMSM may behave not as expected.")
            time.sleep(delay)

            # No need to catch the WorldIsOfflineError, since we check the
            # status.
            self._world.open_console()
        else:
            print("{} - console:".format(self._world.name()))
            print("\t", "FAILURE: The world is offline.")
        return None
    
    def start(self):
        """
        Starts the server.

        See also:
            * WorldWrapper.start()
        """
        try:
            self._world.start()
        except emsm.worlds.WorldStartFailed:
            print("{} - start:".format(self._world.name()))
            print("\t", "FAILURE: The world could not be started.")
        else:
            print("{} - start:".format(self._world.name()))
            print("\t", "The world is now online.")
        return None

    def kill_processes(self):
        """
        Kills all server processes of the world.

        See also:
            * WorldWrapper.kill_processes()
        """
        try:
            self._world.kill_processes()
        except emsm.worlds.WorldStopFailed:
            print("{} - kill-processes:".format(self._world.name()))
            print("\t", "FAILURE: The world could not be stopped.")
        else:
            print("{} - kill-processes:".format(self._world.name()))
            print("\t", "The world is now offline.")
        return None        

    def stop(self, force_stop=False):
        """
        Stops the server.

        Parameters:
            * force_stop
                If *true*, the ``kill processess`` is called if the
                server did not react on the normal shutdown command.
                
        See also:
            * WorldWrapper.stop()
        """
        print("{} - stop:".format(self._world.name()))
        try:
            self._world.stop(force_stop=force_stop)
        except emsm.worlds.WorldStopFailed:
            if force_stop:
                print("\t", "FAILURE: The world could not be stopped.")
            else:
                print("\t", "FAILURE: The world could not be stopped.")
                print("\t", "         Try: *--force-stop*")
        else:
            print("\t", "The world is now offline.")
        return None    

    def restart(self, force_restart=False):
        """
        Restarts the world.

        Parameters:
            * force_restart
                If true, the stop of the world is force by *kill processes*
                if necessairy.

        See also:
            * WorldWrapper.restart()
        """
        print("{} - restart:".format(self._world.name()))
        try:
            self._world.restart(force_restart=force_restart)
        except emsm.worlds.WorldStopFailed:
            if force_stop:
                print("\t", "FAILURE: The world could not be stopped.")
            else:
                print("\t", "FAILURE: The world could not be stopped.")
                print("\t", "         Try: *--force-restart*")
        except emsm.worlds.WorldStartFailed:
            print("{} - start:".format(self._world.name()))
            print("\t", "FAILURE: The world could not be started.")
        else:
            print("\t", "The world has been restarted and is now online.")
        return None

    def uninstall(self):
        """
        Removes the world from EMSM.

        See also:
            * WorldWrapper.uninstall()
        """
        print("{} - uninstall:".format(self._world.name()))
        
        # Make sure, that the user wants to remove the world.
        prompt = "\t Are you sure, that you want to remove the world?"

        if emsm.lib.userinput.ask(prompt):
            self._world.uninstall()
            print("\t", "The world has been removed.")
        else:
            print("\t", "FAILURE: Aborted by user.")
        return None

    
class Worlds(BasePlugin):

    VERSION = "3.0.0-beta"

    DESCRIPTION = __doc__

    def __init__(self, application, name):
        """
        """
        BasePlugin.__init__(self, application, name)

        self.setup_conf()
        self.setup_argparser()
        return None

    def setup_conf(self):
        """
        Loads the configuration values and makes sure they have a valid value.
        """
        conf = self.conf()
        
        # Load the values.
        self._default_log_start = conf.getint(
            "default_log_start", 0)
        self._default_log_limit = conf.getint(
            "default_log_limit", 10)
        self._default_open_console_delay = conf.getint(
            "open_console_delay", 1)
        self._default_send_command_timeout = conf.getint(
            "send_command_timeout", 10)

        # And store the *used* values in the configuration.
        # This makes sense since we initialise the configuration section
        # this way and overwrite invalid values catch by *get()* above.
        conf["default_log_start"] = str(self._default_log_start)
        conf["default_log_limit"] = str(self._default_log_limit)
        conf["open_console_delay"] = str(self._default_open_console_delay)
        conf["send_command_timeout"] = str(self._default_send_command_timeout)
        return None

    def setup_argparser(self):
        """
        Adds the accepted arguments to the argpaser of this plugin.
        """
        parser = self.argparser()
        
        parser.description = "Manage and interact with a world."

        # Information about the world.
        parser.add_argument(
            "--configuration",
            action = "count",
            dest = "configuration",
            help = "Prints the configuration section."
            )
        parser.add_argument(
            "--directory",
            action = "count",
            dest = "directory",
            help = "Prints the path to the world's directory."
            )
        
        parser.add_argument(
            "--log",
            action = "count",
            dest = "log",
            help = "Prints the log."
            )
        parser.add_argument(
            "--log-start",
            action = "store",
            dest = "log_start",
            type = int,
            help = "First printed line of the log. "\
            "('\"-2\"' starts with the 2nd last line)"
            )
        parser.add_argument(
            "--log-limit",
            action = "store",
            dest = "log_limit",
            type = int,
            help = "The number of lines that will be printed."
            )

        parser.add_argument(
            "--pid",
            action = "count",
            dest = "pid",
            help = "Prints the pid of the server that runs the world."
            )
        parser.add_argument(
            "--status",
            action = "count",
            dest = "status",
            help = "Prints the status of the world."
            )
        
        # XXX: I need a name for those group
        # of arguments.
        con_iface_group = parser.add_mutually_exclusive_group()
        con_iface_group.add_argument(
            "--send",
            action = "store",
            dest = "send",
            metavar = "COMMAND",
            help = "Sends the command to the world. E.g.: '\"say Hello\"'"
            )
        con_iface_group.add_argument(
            "--verbose-send",
            action = "store",
            dest = "verbose_send",
            metavar = "COMMAND",
            help = "Sends the command to the world prints the log echo."
            )
        con_iface_group.add_argument(
            "--console",
            action = "count",
            dest = "console",
            help = "Opens the server console of the world."
            )
        
        # Status changes
        group_status_change = parser.add_mutually_exclusive_group()
        group_status_change.add_argument(
            "--start",
            action = "count",
            dest = "start",
            help = "Starts the world."
            )
        group_status_change.add_argument(
            "--stop",
            action = "count",
            dest = "stop",
            help = "Stops the world."
            )
        group_status_change.add_argument(
            "--force-stop",
            action = "count",
            dest = "force_stop",
            help = "Like --stop, but kills the processes "\
            "if the smooth stop fails."
            )
        group_status_change.add_argument(
            "--kill",
            action = "count",
            dest = "kill",
            help = "Kills the processes of the world. I recommend to use "\
            "the force-stop method if you can. force-stop saves the world, "\
            "before it kills the process."
            )
        group_status_change.add_argument(
            "--restart",
            action = "count",
            dest = "restart",
            help = "Restarts the world. If the world is offline, "\
            "the world will be started."
            )
        group_status_change.add_argument(
            "--force-restart",
            action = "count",
            dest = "force_restart",
            help = "Like --restart, but kills the processes to "\
            "stop the world if the smooth stop fails."
            )
        
        # Setup
        parser.add_argument(
            "--uninstall",
            action = "count",
            dest = "uninstall",
            help = "Uninstalls the world."
            )
        return None    

    def run(self, args):
        """
        """
        worlds = self.app().worlds().get_selected()
        for world in worlds:
            world = MyWorld(self.app, world)

            # configuration
            if args.configuration:
                world.print_conf()

            if args.directory:
                world.print_directory()

            # log
            if args.log is not None\
               or args.log_start is not None \
               or args.log_limit is not None:

                if args.log_start is None:
                    args.log_start = self._default_log_start
                if args.log_limit is None:
                    args.log_limit = self._default_log_limit                    
                world.print_latest_log(args.log_start, args.log_limit)

            # pid / status / ...
            if args.pid:
                world.print_pids()
                
            if args.status:
                world.print_status()

            # send / screen / ...
            if args.send:
                world.send_command(args.send)
            elif args.verbose_send:
                world.verbose_send_command(
                    args.verbose_send, self._default_send_command_timeout
                    )
            elif args.console:
                world.open_console(self._default_open_console_delay)

            # start / stop / ...
            if args.start:
                world.start()
            elif args.stop:
                world.stop()
            elif args.force_stop:
                world.stop(force_stop=True)
            elif args.kill:
                world.kill_processes()
            elif args.restart:
                world.restart()
            elif args.force_restart:
                world.restart(force_restart=True)
            # Setup
            if args.uninstall:
                world.uninstall()
        return None
