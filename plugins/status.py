#!/usr/bin/python3

# Extendable Minecraft Server Manager - EMSM
# Copyright (C) 2013-2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
About
=====
This plugin is passive and does not send any command to a server. Furthermore,
it never changes the status of a world. It only creates a status report for each
world and distributes it via email or json.

This plugin creates always a complete status report. This means, that the status
of *all* worlds is included.

Configuration
=============

[status]
email_to = root
email_from = minecraft
email_stmp_starttls = yes
email_smtp_host = localhost
email_smtp_port = 25
email_smtp_user = 
email_smtp_pass = 
json_autorun = no
json_path = 

Where:
------
    * email_to
        Is the recipient of the mail.
    * email_from
        Is the sender of the mail
    * email_smtp_starttls
        Will result in the use of STARTTLS if 'yes'.
    * email_stmp_host
        Is the hostname of the stmp server.
    * email_smtp_port
        Is the port of the smtp server
    * email_smtp_user
        Is the username that is used to auth the client at the smtp server.
    * email_stmp_pass
        Is the password used to auth the client at the smtp server.
    * json_autorun
        If yes, the json status file will be updated each time, the EMSM runs.
    * json_path
        Alternative path for the json status file. The default path is the
        plugins data folder.


Arguments
=========
* --json
    Creates the json status report.
* --mail
    Creates the status report and sends it per mail.
"""


# Modules
# ------------------------------------------------
import time
import smtplib
import email
import email.mime.text
import json
import os
import re
import collections
import datetime

# local
from base_plugin import BasePlugin
from app_lib import userinput, pprinttable


# Backwards compatibility
# ------------------------------------------------
try:
    FileNotFoundError
except:
    FileNotFoundError = OSError
    PermissionError = OSError


# Classes
# ------------------------------------------------
PLUGIN = "Status"


# Classes
# ------------------------------------------------
class WorldStatus(object):
    """
    Summarizes the current status of a world.
    """

    def __init__(self, app, world):
        self.app = app
        self.world = world

        # Frequently used attributes to get the status
        self.name = world.name
        self.log = world.get_log()
        self.properties = world.get_properties()

        # Collect the status information.
        self.status = collections.OrderedDict()
        if world.is_online():
            self.status["status"] = "online"
            self.status["uptime"] = self._get_uptime()
            self.status["players"] = self._get_players()
            # The world could be new, so it's wise to use *.get()*
            self.status["max-players"] = self.properties.get("max-players", -1)
        else:
            self.status["status"] = "offline"
            self.status["uptime"] = self._get_uptime()
        return None

    def _get_uptime(self):
        """
        Returns the uptime of the server in seconds. -1 if the world
        is offline.
        """
        if self.world.is_offline():
            return -1
        
        # Extract the timestamp from the first log entry.
        tmp = self.log[:self.log.find("\n")]
        tmp = tmp[:19]
        try:
            tmp = datetime.datetime.strptime(tmp, "%Y-%m-%d %H:%M:%S")
            uptime = datetime.datetime.now() - tmp
        except ValueError:
            uptime = -1
        return uptime

    def _get_players(self):
        """
        Returns a list with the names of the players, that are currently
        playing on this world.
        """
        if self.world.is_offline():
            return list()
        
        # Parsing the log is faster than using the *list* command.
        regex_login = "\[INFO\] (.*) joined the game"
        regex_quit = "\[INFO\] (.*) left the game"

        logins = re.findall(regex_login, self.log)
        quits = re.findall(regex_quit, self.log)

        # Count the logins and quits and compute the diffrence.
        logins = collections.Counter(logins)
        quits = collections.Counter(quits)
        players = logins - quits
        return list(players)

    # Output
    # --------------------------------------------

    def to_text(self):
        """
        Returns the status formatted as ascii text.
        """
        body = list(self.status.items())
        table_printer = pprinttable.TablePrinter(alignment="<")
        table = table_printer.to_string(body)
        
        text = "{}:\n{}".format(self.name, table)
        return text

        
class Status(BasePlugin):
    """
    Creates a status report of all worlds and stores it as json or
    sends it via mail to a given recipient.
    """

    version = "2.0.0"
    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)

        self.setup_conf()
        self.setup_argparser()
        return None

    def setup_conf(self):
        """Loads the configuraiton and inits the conf."""
        self.email = dict()
        self.email["to"] = self.conf.get("email_to", "root")
        self.email["from"] = self.conf.get("email_from", "minecraft")
        self.email["smtp_starttls"] = self.conf.getboolean(
            "email_smtp_starttls", True)
        self.email["smtp_host"] = self.conf.get("email_smtp_host", "localhost")
        self.email["smtp_port"] = self.conf.getint("email_smtp_port", 25)
        self.email["smtp_user"] = self.conf.get("email_smtp_user", "")
        self.email["smtp_pass"] = self.conf.get("email_smtp_pass", "")

        self.json = dict()
        self.json["auto_run"] = self.conf.getboolean("json_auto_run", False)
        self.json["path"] = self.conf.get("json_path", "")

        # Save all
        conf_bool = lambda b: "yes" if b else "no"

        self.conf["email_to"] = str(self.email["to"])
        self.conf["email_from"] = str(self.email["from"])
        self.conf["email_smtp_starttls"] = conf_bool(self.email["smtp_starttls"])
        self.conf["email_smtp_host"] = str(self.email["smtp_host"])
        self.conf["email_smtp_port"] = str(self.email["smtp_port"])
        self.conf["email_smtp_user"] = str(self.email["smtp_user"])
        self.conf["email_smtp_pass"] = str(self.email["smtp_pass"])

        self.conf["json_autorun"] = conf_bool(self.json["auto_run"])
        self.conf["json_path"] = self.json["path"]
        return None

    def setup_argparser(self):
        self.argparser.add_argument(
            "--json",
            action="count",
            dest="json",
            help="Updates the json status file.")
        
        self.argparser.add_argument(
            "--mail",
            action="count",
            dest="mail",
            help=("Sends a mail with the status report using the "
                  "configuration parameters.")
            )
        return None

    # Status
    # --------------------------------------------

    def _mail(self, status):
        """
        Encodes the status and sends them to the recipients given by
        configuration.
        """
        # Create the message
        text = [
            "EMSM - Status report of your minecraft worlds.",
            "==============================================",
            "",
            "Time: {}".format(time.ctime()),
            "",
            ""]
        text.extend([world.to_text() for world in status])
        text = "\n".join(text)

        msg = email.mime.text.MIMEText(text)
        msg["Subject"] = "EMSM - Status report"
        msg["From"] = self.email["from"]
        msg["To"] = self.email["to"]

        # Send the mail
        smtp = smtplib.SMTP()
        try:
            # Try to connect
            smtp.connect(self.email["smtp_host"], self.email["smtp_port"])
            if self.email["smtp_starttls"]:
                smtp.starttls()
            # And try to login if neccesairy. If the auth fails, try to
            # continue and leave a warning in the log.
            if self.email["smtp_user"]:
                try:
                    smtp.login(self.email["smtp_user"], self.email["smtp_pass"])
                except (smtplib.SMTPHeloError, smtplib.SMTPAuthenticationError):
                    self.log.warning("STMP Authentication failed.",
                                     exc_info=True)
            # Try to send the mail
            smtp.send_message(msg)
        except smtplib.SMTPConnectError as err:
            err_msg = "Could not connect to the smtp-server."
            self.log.error(err_msg, exc_info=True)
        except smtplib.SMTPRecipientsRefused as err:
            err_msg = "Could not send the mail to all recipients."
            self.log.error(err_msg, exc_info=True)
        except smtplib.SMTPException:
            err_msg = "Could not send the status report."
            self.log.error(err_msg, exc_info=True)
        finally:
            try:
                smtp.quit()
            except smtplib.SMTPServerDisconnected:
                pass
        return None

    def _json(self, status):
        """
        Encodes the status as json and saves the json string.
        """
        def default_serializer(o):
            if isinstance(o, datetime.timedelta):
                return o.total_seconds()
            raise TypeError()
        
        tmp = {world.name: world.status \
               for world in status}            
        json_str = json.dumps(tmp, default=default_serializer)
        
        try:
            with open(os.path.join(self.data_dir, "status.json"), "w") as file:
                file.write(json_str)

            if self.json["path"]:
                path = os.path.expanduser(self.json["path"])
                with open(path, "w") as file:
                    file.write(json_str)
        except (FileNotFoundError, PermissionError, IOError) as err:
            msg = "Could not create the json status file."
            self.log.error(msg, exc_info=True)
        return None
        
    # Run
    # --------------------------------------------
    
    def run(self, args):
        """
        Creates always a complete status report. This means, that all worlds
        are included.
        """
        status = [WorldStatus(self.app, world) \
                  for world in self.app.worlds.get_all()]

        if args.mail:
            self._mail(status)
        if args.json:
            self._json(status)
        return None

    def finish(self):
        """
        FooBarBaz
        """
        status = [WorldStatus(self.app, world) \
                  for world in self.app.worlds.get_all()]
        if self.json["auto_run"]:
            self._json(status)
        return None
