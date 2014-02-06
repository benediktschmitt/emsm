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
=====
Extends the EMSM by a backup manager.


Configuration
=============
[backups]
archive_format = bztar
restore_message = This world is about to be ressetted to an earlier state.
restore_delay = 5
max_storage_size = 30
auto_sync = yes
mirrors =

Where
-----
* archive_format
    Is the name of the archive format that should be used to create a
    backup. This string has to be listed in *shutil.get_archive_formats()*.
    Usually, there should be at least *zip* or *tar* available.
* restore_message
    Is send to the world's chat before restoring the world.
* restore_delay
    Seconds between sending the *restore_message* to the chat and starting
    the restore.
* max_storage_size
    Maximum number of backups in the storage folder, before older backups
    will be removed.
* auto_sync
    If yes, the backup mirrors will be sync each time the EMSM runs.
* mirrors
    Comma (,) separated list of the backup directories.


Arguments
=========
The functions are applied to all selected worlds.

* --list
    Lists all available backups.
* --sync
    Synchronises all backups mirrors.
* --create
    Creates a new backup.
* --restore PATH
    Restores the worlds with the backup from the given path.
* --restore-latest
    Restores, if available, the latest backup of the world.
* --restore-menu
    Opens a menu, where the user can select which backup he wants to restore.
"""


# Modules
# ------------------------------------------------
import os
import time
import shutil
import datetime
import tempfile

# local
import world_wrapper
import configuration
from base_plugin import BasePlugin
from app_lib import pprinttable
from app_lib import userinput


# Backward compatibility
# ------------------------------------------------
try:
    FileExistsError
except NameError:
    FileExistsError = OSError

    
# Data
# ------------------------------------------------
PLUGIN = "BackupManager"
AVLB_ARCHIVE_FORMATS = [name for name, desc in shutil.get_archive_formats()]



# Classes
# ------------------------------------------------
class WorldBackupManager(object): 
    """
    Wraps a world to manage the backups of the world.
    """
    
    def __init__(self, app, world,
                 backup_dirs, archive_format, max_storage_size):
        self.app = app
        self.world = world

        # I assume that the BackupManager checked those values.
        self.backup_dirs = backup_dirs 
        self.archive_format = archive_format
        self.max_storage_size = max_storage_size

        # Create the backup directories if they don't exist.
        for path in self.backup_dirs:
            try:
                os.makedirs(path)
            except FileExistsError:
                pass
        return None
    
    # about the filenames
    # --------------------------------------------

    # This backup manager uses the filenames to store the timestamp of the
    # backup.
    # If a filename endswith ".tmp" it is considered as a temporary file.
    
    def get_filename_format(self):
        """
        Returns a string that can be formatted with the datetime method
        strftime.
        The filename has no extension.
        """
        filename_format = "%Y_%m_%d-%H_%M_%S-{}".format(self.world.name)
        return filename_format

    def extract_filename(self, path):
        """
        Extracts the filename from the path and removes the extensions.
        E.g.:
        /foo/bar/foo_class.tar.bz2 -> foo_class
        """
        temp = os.path.basename(path)
        temp = os.path.splitext(temp)
        while temp[1]:
            temp = os.path.splitext(temp[0])
        return temp[0]
        
    def get_date_from_filename(self, filename):
        """
        Extracts the date from the filename. Returns a datetime instance
        if successful, else None.
        """
        filename = self.extract_filename(filename)
        filename_format = self.get_filename_format()
        try:
            return datetime.datetime.strptime(filename, filename_format)
        except ValueError:
            return None

    def get_filename(self, datetime_obj=None):
        """
        Returns the filename of the backup that has been created at the
        datetime index.
        If datetime is None, the current time will be used.
        The returned filename has no extension.
        """
        if datetime_obj is None:
            datetime_obj = datetime.datetime.now()
        filename_format = self.get_filename_format() 
        filename = datetime_obj.strftime(filename_format)
        return filename
    
    # about the storage
    # --------------------------------------------
    
    def get_backups_in_directory(self, directory):
        """
        Returns a dictionary with all existing backups in the directory.
        date => path
        """
        backups = dict()
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if not os.path.isfile(path):
                continue
            if path.endswith(".tmp"):
                continue
            
            date = self.get_date_from_filename(filename)            
            if date is not None:
                path = os.path.join(directory, filename)
                backups[date] = path
        return backups

    def get_backups(self):
        """
        Returns a dictionary with all existing backups.
        """
        backups = dict()
        # In reversed range, backups that exist in the less prior
        # directories will be overwritten by the backups in the storages
        # with an higher priority.
        for directory in reversed(self.backup_dirs):
            temp_backups = self.get_backups_in_directory(directory)
            backups.update(temp_backups)
        return backups

    def get_latest_backup(self):
        """
        Returns (date, path) of the latest backup. If no backup is available,
        None will be returned.
        """
        backups = self.get_backups()
        if not backups:
            return None
        date = max(backups)
        path = backups[date]
        return (date, path)

    def sync(self):
        """
        Synchronises all backup directories and removes the oldest backup
        files until there are less or equal backups as max_storage_size.

        Returns a dictionary that contains the changes for each directory.
        """
        # Get the backups that should remain.
        all_backups = self.get_backups()

        # Get the max_storage_size latest backups.
        to_remain = list(all_backups.keys())
        to_remain.sort(reverse=True)
        to_remain = to_remain[:self.max_storage_size]        
        remaining_backups = {date: all_backups[date] for date in to_remain}
        
        # Synchronise the directories and save the changes.
        changes = dict()
        for directory in self.backup_dirs:
            backups_in_directory = self.get_backups_in_directory(directory)

            changes[directory] = dict()
            changes[directory]["added"] = list()
            changes[directory]["removed"] = list()
            
            # Copy new backups. Copy the backup into a temporary file
            # and rename it, if the copy procedure was successful.
            for date in remaining_backups:
                if date not in backups_in_directory:
                    src = remaining_backups[date]
                    dst = os.path.join(
                        directory, os.path.basename(remaining_backups[date]))
                    tmp_dst = dst + ".tmp"
                    
                    shutil.copy(src, tmp_dst)
                    os.rename(tmp_dst, dst)
                    changes[directory]["added"].append(date)
                    
            # Remove old backups.
            for date in backups_in_directory:
                if date not in remaining_backups:
                    path = backups_in_directory[date]
                    os.remove(path)
                    changes[directory]["removed"].append(date)

            # Remove temporary files from unsuccessful syncs.
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                if path.endswith(".tmp") and os.path.isfile(path):
                    os.remove(path)
        return changes

    # create / restore
    # --------------------------------------------------
    
    def create(self, pre_backup_message=str(), post_backup_message=str()):
        """
        Creates a backup of the world and returns the name of the created
        backup.
        """
        backup_filename = self.get_filename()
        backup_directory = self.backup_dirs[0]
        try:
            # We need to disable the auto-save for the backup. I'm paranoid,
            # so I'disable auto-save in this try-catch construct.
            if self.world.is_online():
                self.world.send_command("say {}".format(pre_backup_message))
                self.world.send_command("save-all")
                self.world.send_command("save-off")
                
            with tempfile.TemporaryDirectory() as temp_dir:                
                backup = shutil.make_archive(
                    base_name = os.path.join(temp_dir, backup_filename),
                    format = self.archive_format,
                    root_dir = self.world.directory,
                    base_dir = "./"
                )

                # Save move
                dst = os.path.join(backup_directory, os.path.basename(backup))
                tmp_dst = dst + ".tmp"
                shutil.move(backup, tmp_dst)
                os.rename(tmp_dst, dst)
                
        # Make sure, that auto save is enabled.
        finally:
            if self.world.is_online():
                self.world.send_command("save-on")
                self.world.send_command("say {}".format(post_backup_message))

        self.sync()
        return os.path.basename(backup)

    def restore(self, backup_file, message=str(), delay=0):
        """
        Restores the backup backup_file.

        Raises: WorldError
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            shutil.unpack_archive(
                filename = backup_file,
                extract_dir = temp_dir
                )
            
            # Stop the world.
            was_online = self.world.is_online()
            if was_online:
                self.world.send_command("say {}".format(message))
                time.sleep(delay)
                self.world.kill_processes()

            # Delete the world and restore the backup.
            for i in range(5):
                # XXX: Fixes an error with server.log.lck
                # and shutil.rmtree(...).
                try:
                    shutil.rmtree(self.world.directory)
                    break
                except OSError:
                    time.sleep(0.05)
            shutil.copytree(temp_dir, self.world.directory)
            
        if was_online:
            self.world.start()
        return None


class VerboseWorldBackupManager(WorldBackupManager):
    """
    Extends the WorldBackupManager for the command line interface.
    """

    # about the storage
    # --------------------------------------------------
    
    def list_backups(self):
        """
        Prints a table with all existing backups.
        """
        backups = self.get_backups()

        if backups:
            printer = pprinttable.TablePrinter("Nr.", "<")
            body = [(date.ctime(), path) for date, path in backups.items()]
            body.sort()
            head = ["date", "path"]
            
            print("{} - list-backups:".format(self.world.name))
            printer.print(body, head)
        else:
            print("{} - list-backups: There is no backup available."\
                  .format(self.world.name))
        return None            

    def sync(self, show_changes=False):
        """
        Synchronises the backups in the diffrent storages.
        """
        changes = WorldBackupManager.sync(self)

        # Skip if not explicitly called.
        if not show_changes:
            return None

        # Prints the changes in an hierarchy.
        print("{} - sync:".format(self.world.name))
        for directory in changes:
            added = changes[directory]["added"]
            removed = changes[directory]["removed"]
            
            print(4*" ", "o", directory)        
            if not (added or removed):
                print(8*" ", "->", "no changes")
            if added:
                print(8*" ", "o", "added:")
                for e in added:
                    print(12*" ", "o", e)
            if removed:
                print(8*" ", "o", "removed:")
                for e in removed:
                    print(12*" ",  "o", e)
        return None
    
    # create / restore
    # --------------------------------------------------
    
    def create(self):
        """
        Creates a new backup.
        """
        backup = WorldBackupManager.create(self)
        print("{} - create: The backup '{}' has been created."\
              .format(self.world.name, backup))
        return None

    def _verify_restore(self):
        """
        Asks the user if he really wants to restore a world.
        """
        question = "Do you really want to restore the world '{}'? "\
                   "The current world will be removed! "\
                   .format(self.world.name)
        return userinput.ask(question, default=False)
                
    def restore(self, backup_file, message, delay, ask=True):
        # Verify the restore command.
        if ask and not self._verify_restore():
            return None

        print("{} - restore: Using '{}' as backup file."\
              .format(self.world.name, backup_file))
        try:
            WorldBackupManager.restore(self, backup_file, message, delay)
        except world_wrapper.WorldStopFailed:
            print("{} - restore: failure: The world could not be stopped."\
                  .format(self.world.name))
        except world_wrapper.WorldStartFailed:
            print("{} - restore: failure: The world could not be restarted."\
                  .format(self.world.name))
        except Exception as error:
            print("{} - restore: failure: An unexpected error occured: {}"\
                  .format(self.world.name, error))
            raise
        else:
            print("{} - restore: Restore is complete."\
                  .format(self.world.name))
        return None
    
    def restore_latest(self, message, delay):
        """
        Restores the latest available backup of the world.
        """
        temp = self.get_latest_backup()

        # Break, if no backup is available.
        if temp is None:
            print("{} - restore-latest: failure: there's no backup available."\
                  .format(self.world.name))
            return None

        # Continue with the restore process.
        date, backup = temp
        print("{} - restore-latest: latest backup created at '{}'"\
              .format(self.world.name, date))
        return self.restore(backup, message, delay)

    def restore_menu(self, message, delay):
        """
        Prints a table with all existing backups and lets the user select
        the backup that should be restored.
        """
        backups = self.get_backups()
        backups = list(backups.items())

        # Break if there is no backup available.
        if not backups:
            print("{} - restore-menu: failure: there is no backup available."\
                  .format(self.world.name))
            return None

        # Continue with the restore.
        body = [[date.ctime()] for date, path in backups]
        head = ["date"]
        table_printer = pprinttable.TablePrinter("Nr.", "<")
        table_printer.print(body, head)
        
        backup = userinput.get_value(
            prompt="Select the backup that you want to restore: ",
            conv_func=lambda s: int(s.strip()),
            check_func=lambda s: s in range(len(backups))
            )
        date, backup = backups[backup]
        return self.restore(backup, message, delay)
    
    
class BackupManager(BasePlugin):
    """
    Provides methods to create backups of the worlds and to restore them.
    """
    
    version = "2.0.0"
    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)
        
        self.setup_conf()
        self.setup_argparser()
        return None

    def setup_conf(self):
        # Some configurable stuff        
        self.archive_format = self.conf.get("archive_format", "bztar")
        if not self.archive_format in AVLB_ARCHIVE_FORMATS:
            self.archive_format = "tar"

        self.restore_message = self.conf.get(
            "restore_message",
            "This world is about to be ressetted to an earlier state.")
        
        self.restore_delay = self.conf.getint("restore_delay", 5)
        self.restore_delay = max(0, self.restore_delay)
        
        self.auto_sync = self.conf.getboolean("auto_sync", True)

        self.max_storage_size = self.conf.getint("max_storage_size", 30)        
        self.max_storage_size = max(1, self.max_storage_size)
        
        # We need rw access in the backup directories.
        self.mirrors = list()
        for path in self.conf.get("mirrors", "").split(","):
            path = path.strip()
            if not path:
                continue            
            path = os.path.expanduser(path)
            if not os.access(path.strip(), os.F_OK | os.W_OK | os.R_OK):
                message = "The backup mirror '{}' does not exist or this "\
                          "script has not sufficient rights in the directory."\
                          .format(path)
                raise configuration.ValueError_("mirrors", self.name, "", message)
            self.mirrors.append(path)

        # Let's init the configuration section.
        self.conf["archive_format"] = str(self.archive_format)
        self.conf["restore_message"] = str(self.restore_message)
        self.conf["restore_delay"] = str(self.restore_delay)  
        self.conf["auto_sync"] = "yes" if self.auto_sync else "no"
        self.conf["max_storage_size"] = str(self.max_storage_size)
        self.conf["mirrors"] = ",\n\t".join(self.mirrors)

        # Some other vars.
        self.backup_dirs = [self.data_dir] + self.mirrors
        return None
    
    def setup_argparser(self):
        self.argparser.description = (
            "This plugin provides methods to manage the backups of the worlds."
            )
        
        # We want to allow only one action per run.
        me_group = self.argparser.add_mutually_exclusive_group()

        # Storage
        me_group.add_argument(
            "--list",
            action = "count",
            dest = "list",
            help = "Lists all available backups."
            )
        me_group.add_argument(
            "--sync",
            action = "count",
            dest = "sync",
            help = "Synchronises and cleans the backup directories."
            )

        # Create
        me_group.add_argument(
            "--create",
            action = "count",
            dest = "create",
            help = "Creates a backup."
            )

        # Restore
        me_group.add_argument(
            "--restore",
            action = "store",
            dest = "restore",
            metavar = "PATH",
            help = "Restores the world from the given backup path."
            )
        me_group.add_argument(
            "--restore-latest",
            action = "count",
            dest = "restore_latest",
            help = "Restores the latest backup."
            )
        me_group.add_argument(
            "--restore-menu",
            action = "count",
            dest = "restore_menu",
            help = "Opens a menu where the backup that should be restored, "\
            "can be selected and restores the backup."
            )
        return None
    
    def uninstall(self):
        super().uninstall()
        
        question = "{} - Do you want to remove the mirror directories?"\
                   .format(self.name)
        if userinput.ask(question, False):
            for path in self.mirrors:
                shutil.rmtree(path)
        return None

    # backup manager
    # --------------------------------------------------
    
    def get_backup_manager(self, world):
        """
        Returns an initialised backup manager for the world.
        """
        backup_dirs = [os.path.join(path, world.name) \
                       for path in self.backup_dirs]
        
        world = VerboseWorldBackupManager(
            self.app, world, backup_dirs,
            self.archive_format, self.max_storage_size)
        return world

    # plugin
    # -------------------------------------------------- 

    def run(self, args):
        worlds = self.app.worlds.get_selected()
        for world in worlds:
            world = self.get_backup_manager(world)

            if args.list:
                world.list_backups()
                
            elif args.sync:
                world.sync(show_changes=True)
                
            elif args.create:
                world.create()
                
            elif args.restore:
                backup = args.restore
                world.restore(backup, self.restore_message, self.restore_delay)
                
            elif args.restore_latest:
                world.restore_latest(self.restore_message, self.restore_delay)

            elif args.restore_menu:
                world.restore_menu(self.restore_message, self.restore_delay)
        return None


    def finish(self):
        """
        Makes sure that all backup directories are synchronised.
        """
        if not self.auto_sync:
            return None

        worlds = self.app.worlds.get_all()
        for world in worlds:
            world = self.get_backup_manager(world)            
            world.sync()
        return None
