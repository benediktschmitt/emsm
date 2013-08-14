#!/usr/bin/env python


# Modules
# ------------------------------------------------
import socket
import re
import time

# local
from _common_lib import userinput

# local (from the application)
import world_wrapper
from base_plugin import BasePlugin


# Data
# ------------------------------------------------
PLUGIN = "Angel"


def check_port(port, ip="", timeout=1):
    """
    Returns `true` if the tcp address *ip*:*port* is
    reachable.
    """
    adr = (ip, port)
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(adr)
    except socket.error:
        return False
    else:
        return True
    finally:
        s.close()


def world_is_listening(world, attempts=10, sleep_intervall=1):
    """
    Returns `true`, if the *world* is listening
    on it's address.
    """
    properties = world.get_properties()
    ip = properties.get("server-ip", "")
    port = properties.get("server-port", "")
    port = int(port) if port.isdigit() else 25565

    for i in range(attempts):
        if check_port(port, ip):
            return True
    return False

    
# Classes
# ------------------------------------------------   
class Angel(BasePlugin):
    """
    Makes sure, that the world is running at each run.
    
    """

    finish_priority = 1000
    version = "1.0.0"
    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)

        # Whats to do if a world is offline.
        self.error_action = self.conf.get("error_action")
        if self.error_action not in ("none", "restart", "stop", "stdout"):
            self.error_action = "none"

        self.error_regex = self.conf.get("error_regex", "(\[SEVERE\])")
        self.auto_run = self.conf.getboolean("auto_run", False)
        self.guard_all_worlds = self.conf.getboolean("guard_all_worlds", False)
             
        self.conf["error_action"] = self.error_action        
        self.conf["error_regex"] = self.error_regex
        self.conf["auto_run"] = "yes" if self.auto_run else "no"
        self.conf["guard_all_worlds"] = "yes" if self.guard_all_worlds else "no"
        return None

    def uninstall(self):
        """
        Remove the additional configuration options in the worlds.conf.
        """
        worlds_conf = self.application.configuration.worlds
        question = "{} - uninstall: Do you want to remove the additional "\
                   "options in worlds.conf?".format(self.name)
        if userinput.ask(question):
            for section in worlds_conf:
                worlds_conf.remove_option(section, "enable_angel")
        return None                    

    def guard(self):
        """
        Checks if all worlds are running that should be running.
        """
        worlds = self.application.world_manager.get_all_worlds()
        for world in worlds:
            if not (self.guard_all_worlds \
                    or world.conf.getboolean("enable_angel", False)):
                continue
            
            error = world.is_offline()
            # XXX Could be buggy if a world has been restartet.
            error = error or not world_is_listening(world)
            error = error or re.search(self.error_regex, world.get_log())
            
            if error:
                if self.error_action == "restart":
                    if world.is_online():
                        world.stop(force_stop=True)
                    world.start()
                elif self.error_action == "stop":
                    if world.is_online():
                        world.stop(force_stop=True)
                elif self.error_action == "stdout":
                    print("{}: '{}' seems to be offline"\
                          .format(self.name, world.name))
        return None    

    def setup_argparser_argument_group(self, group):
        group.title = self.name
        group.description = "Watches the logfiles and checks if the worlds "\
                            "are online"

        group.add_argument(
            "--guard",
            action="count", dest="guard",
            help="Runs the guardian angel for each world, if configured.")
        return None

    def run(self, args):
        if args.guard:
            self.guard()
        return None

    def finish(self):
        if self.auto_run:
            self.guard()
        return None
