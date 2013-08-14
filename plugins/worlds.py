#!/usr/bin/env python


# Modules
# --------------------------------------------------
import time
import os

# local (from the application)
import world_wrapper
from base_plugin import BasePlugin

# local
from _common_lib import userinput, pprinttable


# Data
# --------------------------------------------------
PLUGIN = "Worlds"


# Classes
# --------------------------------------------------
class MyWorld(object):
    """
    Wraps an application world wrapper :)
    
    """    

    def __init__(self, application, world):
        self.application = application
        self.world = world
        return None

    def print_configuration(self):
        """
        Prints the application's world configuration.
        """
        conf = self.world.conf
        body = [[option, conf[option]] for option in conf]
        body.sort()

        table = pprinttable.table_string(
            body=body,
            header=["option", "value"],
            alignment = "^")
        
        print("{} - configuration:".format(self.world.name))
        print(table)
        return None    
    
    def print_properties(self):
        """
        Prints the content of the server.properties file.
        """
        properties = self.world.get_properties()
        properties = list(properties.items())
        properties.sort()

        table = pprinttable.table_string(
            body = properties,
            header = ["property", "value"],
            alignment = "^")
            
        print("{} - server.properties:".format(self.world.name))
        print(table)
        return None

    def print_log(self, start = 0, limit = 20):
        log = self.world.get_log()
        log = log.split("\n")

        # Make sure that the limits are valid.
        # 0 <= start <= size
        # limit <= size - start
        size = len(log)
        start = max(0, size + start) if start < 0 else min(start, size)
        limit = min(limit, size - start)
        
        log = log[start:start+limit]
        log = "\n".join(log)

        print("{} - server.log - line {}-{}/{}:"\
              .format(self.world.name, start, start + limit, size))
        print(log)
        return None

    def print_pids(self):
        pids = self.world.get_pids()
        pids = ", ".join(pids)

        print("{} - pids: {}".format(self.world.name, pids))
        return None

    def print_status(self, status = None):
        if self.world.is_online():
            temp = "{} - status: online"
        else:
            temp = "{} - status: offline"
        temp = temp.format(self.world.name)
        print(temp)
        return None

    def send_command(self, cmd):
        try:
            self.world.send_command(cmd)
        except world_wrapper.WorldIsOfflineError:
            print("{} - send-command: failure: The world is offline."\
                  .format(self.world.name))
        else:
            print("{} - send-command: The command '{}' has been sended."\
                  .format(self.world.name, cmd))
        return None    
    
    def verbose_send_command(self, cmd, timeout):
        """
        Sends the command to the world and prints the output.
        """
        try:
            output = self.world.send_command_get_output(cmd, timeout)
        except world_wrapper.WorldIsOfflineError:
            print("{} - verbose-send-command: failure: "\
                  "The world is offline."\
                  .format(self.world.name))
        except world_wrapper.WorldCommandTimeout:
            print("{} - verbose-send-command: failure: "\
                  "the world did not react in {}s"\
                  .format(self.world.name, timeout))
        else:
            print("{} - verbose-send-command:".format(self.world.name))
            print(output)
        return None

    
    def open_console(self, delay=1):
        print("Press [ctrl + a + d] to detach from the screen session.")
        print("!!! STOPPING THE WORLD IN THE CONSOLE CAN "\
              "CAUSE UNEXPECTED BEHAVIOUR OF THIS APPLICATION !!!")
        time.sleep(delay)
        try:
            self.world.open_console()
        except world_wrapper.WorldIsOfflineError:
            print("{} - open-console: failure: The world is offline."\
                  .format(self.world.name))
        return None
    
    # start / stop / restart
    # --------------------------------------------
    
    def start(self):
        try:
            self.world.start()
        except world_wrapper.WorldIsOnlineError:
            print("{} - start: failure: The world is already online."\
                  .format(self.world.name))
        except world_wrapper.WorldStartFailed:
            print("{} - start: failure: The world could not be started."\
                  .format(self.world.name))
        else:
            print("{} - start: The world is now online."\
                  .format(self.world.name))
        return None

    def kill_processes(self):
        try:
            self.world.kill_processes()
        except world_wrapper.WorldIsOfflineError: 
            print("{} - kill-processes: failure: "\
                  "The world is already offline.".format(self.world.name))
        except world_wrapper.WorldStopFailed:
            print("{} - kill-processes: failure: "\
                  "The world could not be stopped".format(self.world.name))
        else:
            print("{} - kill-processes: The world is now offline."\
                  .format(self.world.name))
        return None        

    def stop(self, force_stop=False):
        print("{} - stop: ...".format(self.world.name))        
        try:
            self.world.stop(force_stop)
        except world_wrapper.WorldIsOfflineError:
            print("{} - stop: failure: The world is already offline."\
                  .format(self.world.name))
        except world_wrapper.WorldStopFailed:
            print("{} - stop: failure: The world could not be stopped."\
                  .format(self.world.name))
            if not force_stop:
                print("\t", "-> try force-stop")
        else:
            print("{} - stop: The world is now offline."\
                  .format(self.world.name))
        return None    

    def restart(self, force_restart=False):
        print("{} - restart: ...".format(self.world.name))
        # Stop the world.
        try:
            self.world.stop(force_restart)
        except world_wrapper.WorldIsOfflineError:
            pass
        except world_wrapper.WorldStopFailed:
            print("{} - restart: failure: The world could not be stopped."\
                  .format(self.world.name))
            if not force_restart:
                print("\t", "-> try force-restart")
            return None         # <- EXIT
        else:
            print("{} - restart: The world is now offline."\
                  .format(self.world.name))
        # Start the world.
        try:
            self.world.start()
        except world_wrapper.WorldStartFailed:
            print("{} - restart: failure: The world could not be restarted."\
                  .format(self.world.name))
        else:
            print("{} - restart: The world has been restarted."\
                  .format(self.world.name))
        return None
    
    # setup
    # --------------------------------------------
    
    def uninstall(self):
        # Make sure, that the user wants to remove the world.
        question = "Do you really want to remove the world '{}'?"\
                   .format(self.world.name)
        if userinput.ask(question):
            self.world.uninstall()        
        return None

    
class Worlds(BasePlugin):
    """
    Public interface for the world wrapper.

    """

    version = "1.0.0"

    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)

        # Some configuration stuff
        self.default_log_start = self.conf.getint(
            "default_log_start", 0)
        self.default_log_limit = self.conf.getint(
            "default_log_limit", 10)
        self.default_open_console_delay = self.conf.getint(
            "open_console_delay", 1)
        self.default_send_command_timeout = self.conf.getint(
            "send_command_timeout", 10)

        # Let's init the configuration section.
        self.conf["default_log_start"] = str(self.default_log_start)
        self.conf["default_log_limit"] = str(self.default_log_limit)
        self.conf["open_console_delay"] = str(self.default_open_console_delay)
        self.conf["send_command_timeout"] = str(self.default_send_command_timeout)
        return None

    def setup_argparser_argument_group(self, group):
        group.title = self.name
        group.description = "This plugin provides methods to "\
                            "manage the worlds."

        # Information about the world.
        group.add_argument(
            "--configuration",
            action = "count",
            dest = "configuration",
            help = "Prints the configuration section."
            )
        group.add_argument(
            "--properties",
            action = "count",
            dest = "properties",
            help = "Prints the content of the server.properties file."
            )
        
        group.add_argument(
            "--log",
            action = "count",
            dest = "log",
            help = "Prints the log."
            )
        group.add_argument(
            "--log-start",
            action = "store",
            dest = "log_start",
            type = lambda v: int(v.replace("r", "-")),
            help = "The first line of the log that will be printed. "\
            "If r10, the 10th last lines will be the first line that will "\
            "be printed."
            )
        group.add_argument(
            "--log-limit",
            action = "store",
            dest = "log_limit",
            type = int,
            help = "The number of lines that will be printed."
            )
        
        group.add_argument(
            "--pid",
            action = "count",
            dest = "pid",
            help = "Prints the pid of the server that runs the world."
            )
        group.add_argument(
            "--status",
            action = "count",
            dest = "status",
            help = "Prints the status of the world."
            )
        
        # XXX: I need a name for those group
        # of arguments.
        group.add_argument(
            "--send",
            action = "store",
            nargs = "*",
            dest = "send",
            metavar = "CMD",
            help = "Sends the command to the world."
            )
        group.add_argument(
            "--verbose-send",
            action = "store",
            nargs = "*",
            dest = "verbose_send",
            metavar = "CMD",
            help = "Sends the command to the world and "\
            "and prints the log echo."
            )
        group.add_argument(
            "--open-console",
            action = "count",
            dest = "open_console",
            help = "Opens the server console of the world."
            )
        
        # Status changes
        group_status_change = group.add_mutually_exclusive_group()
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
            "--kill-processes",
            action = "count",
            dest = "kill_processes",
            help = "Kills the processes of the world. I recommend to use "\
            "the force-stop method if you can."
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
        group.add_argument(
            "--uninstall",
            action = "count",
            dest = "uninstall",
            help = "Uninstalls the worlds."
            )
        return None    

    def run(self, args):
        """ run """
        # Get the selected worlds
        worlds = self.application.world_manager.get_selected_worlds()

        # And action:
        for world in worlds:

            world = MyWorld(self.application, world)

            # Information about the world.
            if args.configuration:
                world.print_configuration()
                
            if args.properties:
                world.print_properties()
                
            if args.log or args.log_start or args.log_limit:
                if args.log_start is None:
                    args.log_start = self.default_log_start
                if args.log_limit is None:
                    args.log_limit = self.default_log_limit
                world.print_log(args.log_start, args.log_limit)
                
            if args.pid:
                world.print_pids()

            if args.status:
                world.print_status()
                
            # XXX: I need a name for those group
            # of arguments.
            if args.send:
                cmd = " ".join(args.send)
                world.send_command(cmd)

            if args.verbose_send:
                cmd = " ".join(args.verbose_send)
                world.verbose_send_command(
                    cmd, self.default_send_command_timeout)

            if args.open_console:
                world.open_console(self.default_open_console_delay)

            # Status changes
            if args.start:
                world.start()

            if args.stop:
                world.stop()

            if args.force_stop:
                world.stop(force_stop=True)

            if args.kill_processes:
                world.kill_processes()

            if args.restart:
                world.restart()

            if args.force_restart:
                world.restart(force_restart=True)

            # Setup
            if args.uninstall:
                world.uninstall()
        return None
