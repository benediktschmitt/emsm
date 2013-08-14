#!/usr/bin/python3


# Modules
# ------------------------------------------------
import os
import shutil
import datetime
import tempfile
import time

# local (from the wrapper folder)
import world_wrapper
import configuration
from base_plugin import BasePlugin

# local
from _common_lib import pprinttable
from _common_lib import userinput


# Backward compatibility
# ------------------------------------------------
try:
    FileExistsError
except NameError:
    FileExistsError = OSError

    
# Data
# ------------------------------------------------
PLUGIN = "BackupManager"
AVAILABLE_ARCHIVE_FORMATS = [name for name, desc in shutil.get_archive_formats()]


# Classes
# ------------------------------------------------
class WorldBackupManager(object): 
    """
    Wraps a world to manage the backups of the world.
    """
    
    def __init__(self,
                 application,
                 world,
                 backup_directories,
                 archive_format,
                 max_storage_size
                 ):
        self.application = application
        self.world = world

        # I assume that the BackupManager checked those values.
        self.backup_directories = backup_directories 
        self.archive_format = archive_format
        self.max_storage_size = max_storage_size

        # Create the backup directories if they don't exist.
        for path in self.backup_directories:
            try:
                os.makedirs(path)
            except FileExistsError:
                pass
        return None
    
    # about the filenames
    # --------------------------------------------
    
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
            date = self.get_date_from_filename(filename)            
            if date is None:
                continue            
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
        for directory in reversed(self.backup_directories):
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
        to_remain.sort(reverse = True)
        to_remain = to_remain[:self.max_storage_size]        
        remaining_backups = {date: all_backups[date] for date in to_remain}
        
        # Synchronise the directories and save the changes.
        changes = dict()
        for directory in self.backup_directories:
            backups_in_directory = self.get_backups_in_directory(directory)

            changes[directory] = dict()
            changes[directory]["added"] = list()
            changes[directory]["removed"] = list()
            
            # Copy new backups.
            for date in remaining_backups:
                if date not in backups_in_directory:
                    shutil.copy(remaining_backups[date], directory)
                    changes[directory]["added"].append(date)
                    
            # Remove old backups.
            for date in backups_in_directory:
                if date not in remaining_backups:
                    path = backups_in_directory[date]
                    os.remove(path)
                    changes[directory]["removed"].append(date)
        return changes

    # create / restore
    # --------------------------------------------------
    
    def create(self, pre_backup_message=str(), post_backup_message=str()):
        """
        Creates a backup of the world and returns the name of the created
        backup.
        """
        # We need to disable the auto-save for the backup.
        if self.world.is_online():
            self.world.send_command("say {}".format(pre_backup_message))
            self.world.send_command("save-all")
            self.world.send_command("save-off")

        backup_filename = self.get_filename()
        backup_directory = self.backup_directories[0]
        try:
            with tempfile.TemporaryDirectory() as temp_dir:                
                backup = shutil.make_archive(
                    base_name = os.path.join(temp_dir, backup_filename),
                    format = self.archive_format,
                    root_dir = self.world.directory,
                    base_dir = "./"
                )
                shutil.move(backup, backup_directory)                
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
                # XXX: Fixes an error with server.log.lck
                # and shutil.rmtree(...).
                time.sleep(0.05)

            # Restore the world.
            shutil.rmtree(self.world.directory)
            shutil.copytree(temp_dir, self.world.directory)
            
        if was_online:
            self.world.start()
        return None

    # remove
    # --------------------------------------------------
    
    @staticmethod
    def remove_relicts(backup_directories):
        """
        Removes the backup directories. Can be used to remove the backup
        directories of a world that's no longer in the application's
        configuration.
        """
        for path in filter(os.path.exists, backup_directories):
            shutil.rmtree(path, ignore_errors=True)
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
            table = pprinttable.table_string(
                body = list(backups.items()),
                header = ["date", "path"],
                index_name = "Nr.",
                alignment = "<"
                )
            print("{} - list-backups:".format(self.world.name))
            print(table)
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
            
            print(4 * " ", "o", directory)        
            if not (added or removed):
                print(8 * " ", "->", "no changes")
            if added:
                print(8* " ", "o", "added:")
                for e in added:
                    print(12 * " ", "o", e)
            if removed:
                print(8 * " ", "o", "removed:")
                for e in removed:
                    print(12 * " ",  "o", e)
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
        return userinput.ask(question)
                
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
        table = pprinttable.table_string(
            body = [[date] for date, path in backups],
            header = ["date"],
            index_name = "Nr.",
            alignment = "<"
            )
        backup = userinput.get_value(
            prompt = "{}\nSelect the backup that you want to restore: ".format(table),
            conv_func = lambda s: int(s.strip()),
            check_func = lambda s: s in range(len(backups))
            )
        date, backup = backups[backup]
        return self.restore(backup, message, delay)
    
    
class BackupManager(BasePlugin):
    """
    Provides methods to create backups of the worlds and to restore them.

    """
    
    version = "1.0.0"

    default_archive_format = "bztar"    
    default_max_storage_time = 10
    default_auto_sync = False    
    default_restore_message = "This world will be resetted to an earlier state."
    default_restore_delay = 5    

    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)
        
        # Some configurable stuff
        self.max_storage_size = self.conf.getint(
            "max_storage_size", self.default_max_storage_time)
        if self.max_storage_size < 1:
            self.max_storage_size = self.default_max_storage_time
        
        self.auto_sync = self.conf.getboolean(
            "auto_sync", self.default_auto_sync)

        self.restore_message = self.conf.get(
            "restore_message", self.default_restore_message)

        self.restore_delay = self.conf.get(
            "restore_delay", self.default_restore_delay)
        
        self.archive_format = self.conf.get(
            "archive_format", self.default_archive_format)
        if not self.archive_format in AVAILABLE_ARCHIVE_FORMATS:
            self.archive_format = self.default_archive_format
            
        # We need rw access in the backup directories.
        self.mirrors = list()
        for path in self.conf.get("mirrors", "").split(","):
            path = path.strip()
            if not path:
                continue
            
            path = os.path.expanduser(path)
            if not os.access(path.strip(), os.F_OK | os.W_OK | os.R_OK):
                message = "the backup mirror '{}' does not exist or this "\
                          "script has no access to the directory."\
                          .format(path)
                raise configuration.ValueError_("mirrors", self.name, "", message)
            self.mirrors.append(path)

        # Let's init the configuration section.
        self.conf["max_storage_size"] = str(self.max_storage_size)
        self.conf["auto_sync"] = "yes" if self.auto_sync else "no"
        self.conf["archive_format"] = str(self.archive_format)
        self.conf["mirrors"] = ",\n\t".join(self.mirrors)        

        # Some other vars.
        self.backup_directories = [self.data_dir] + self.mirrors
        return None

    def uninstall(self):
        question = "{} - Do you want to remove the mirror directories?"\
                   .format(self.name)
        if userinput.ask(question):
            for path in self.mirrors:
                shutil.rmtree(path)
        return None

    # backup manager
    # --------------------------------------------------
    
    def get_world_backup_directories(self, worldname):
        """
        Returns the backup directories for the world.
        """
        temp = [os.path.join(path, worldname) \
                for path in self.backup_directories]
        return temp

    
    def get_world_backup_manager(self, world):
        """
        Returns an initialised backup manager for the world.
        """
        world = VerboseWorldBackupManager(
            self.application,
            world,
            self.get_world_backup_directories(world.name),
            self.archive_format,
            self.max_storage_size
            )
        return world

    # plugin
    # --------------------------------------------------
    
    def setup_argparser_argument_group(self, group):
        group.title = self.name
        group.description = "This plugin provides methods to "\
                            "manage the backups of the worlds."
        
        # We want to allow only one action per run.
        me_group = group.add_mutually_exclusive_group()

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
            metavar = "BACKUP_PATH",
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

    def run(self, args):
        # Get the selected worlds.
        worlds = self.application.world_manager.get_selected_worlds()
        
        # And action:
        for world in worlds:

            world = self.get_world_backup_manager(world)

            if args.list:
                world.list_backups()

            if args.sync:
                world.sync(show_changes = True)

            if args.create:
                world.create()

            if args.restore:
                backup = args.restore
                world.restore(backup, self.restore_message, self.restore_delay)

            if args.restore_latest:
                world.restore_latest(self.restore_message, self.restore_delay)

            if args.restore_menu:
                world.restore_menu(self.restore_message, self.restore_delay)
        return None


    def finish(self):
        """
        Makes sure that all backup directories are synchronised.
        """
        if not self.auto_sync:
            return None

        worlds = self.application.world_manager.get_all_worlds()
        for world in worlds:            
            world = self.get_world_backup_manager(world)            
            world.sync()
        return None
