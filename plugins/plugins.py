#!/usr/bin/env python


# Modules
# --------------------------------------------------
import os
import shutil
import tempfile
import collections

# local (from the application)
import plugin_manager
from base_plugin import BasePlugin

# local
from _common_lib import userinput


# Data
# --------------------------------------------------
PLUGIN = "Plugins"


# Exceptions
# --------------------------------------------------
class InstallError(Exception):
    """
    Raised from the BaseInstaller.
    """

    def __init__(self, msg):
        self.msg = msg
        return None
    
    def __str__(self):
        return self.msg
    
    
# Classes
# --------------------------------------------------
class BaseUnInstaller(object):
    """
    The base un-/installer.
    """

    def __init__(self, application, plugin):
        self.application = application
        self.plugin = plugin
        return None
    
    def get_plugin_related_paths(self):
        """
        Returns a dictionary that contains the paths of the plugin
        that are used in the application.

        type/purpose => path
        """
        pathsystem = self.application.pathsystem
        
        paths = collections.OrderedDict()        
        paths["plugin"] = os.path.join(
            pathsystem.plugins_source_dir, self.plugin + ".py")
        paths["library"] = os.path.join(
            pathsystem.plugins_source_dir, self.plugin + "_lib")
        paths["data"] = os.path.join(
            pathsystem.plugins_data_dir, self.plugin)
        return paths
    
    
class BaseInstaller(BaseUnInstaller):
    """
    Plugin installer.

    The archive that contains the plugin should have
    the following structure:
    
    \foo.tar.bz2
        \plugin.py
        \readme.txt
        \library
            \bar.py
            \bar1.py
            \...
        \data
            \bar.txt
            \bar.csv
            \...

    The filenames will be adapted to the application
    filenames:
    \app
        \plugins_src
            \foo.py <= plugin.py
            \foo_lib <= library
        \plugins_data
            \foo <= data
    """

    def __init__(self, application, archive):
        # The path to the archive that contains the new plugin.
        self.archive = archive

        # The name of the new plugin.
        plugin = archive[:archive.find(".")]        
        BaseUnInstaller.__init__(self, application, plugin)
        return None    

    def print_readme(self, readme):
        """
        Prints the content of the readme file.
        """
        with open(readme) as file:
            print(file.read())
        return None
    
    def install(self):
        """
        Unpacks the archive with the plugin and moves the files and
        folders to the application's directories.

        Raises: InstallError
        """
        app_paths = self.get_plugin_related_paths()

        # Check if the plugin already exists.
        if self.application.plugin_manager.plugin_is_available(self.plugin):
            msg = "a plugin with the same name has already been "\
                  "installed."
            raise InstallError(msg)

        # Extract the plugin in a temporary directory so that the plugin will
        # not mess up the application's directories if it's not valid.
        with tempfile.TemporaryDirectory() as temp_dir:
            
            try:
                shutil.unpack_archive(
                    filename = self.archive,
                    extract_dir = temp_dir
                    )
            except ValueError as error:
                msg = "the archive could not be unpacked: {}".format(error)
                raise InstallError(msg)

            # Check the files and directories in the temporary directory.
            package_paths = {filename: os.path.join(temp_dir, filename) \
                             for filename in os.listdir(temp_dir)}
            
            if "plugin.py" not in package_paths:
                msg = "the package does not contain the 'plugin.py' file."
                raise InstallError(msg)

            if not os.path.isfile(package_paths["plugin.py"]):
                msg = "'plugin.py' is not a file."
                raise InstallError(msg)

            if "data" in package_paths \
               and not os.path.isdir(package_paths["data"]):
                msg = "'data' is not a directory."
                raise InstallError(msg)

            if "library" in package_paths \
               and not os.path.isdir(package_paths["library"]):
                msg = "'library' is not a directory."
                raise InstallError(msg)

            if "readme.txt" in package_paths \
               and not os.path.isfile(package_paths["readme.txt"]):
                msg = "'readme.txt' is not a file."
                raise InstallError(msg)

            # Move the files.
            shutil.move(package_paths["plugin.py"], app_paths["plugin"])
            if "library" in package_paths:
                shutil.move(package_paths["library"], app_paths["library"])
            if "data" in package_paths:
                shutil.move(package_paths["data"], app_paths["data"])

            # Show the readme.
            if "readme.txt" in package_paths:
                self.print_readme(package_paths["readme.txt"])
        return None

                            
class Installer(BaseInstaller):
    """
    A friendly installer.

    Catches the InstallError exceptions that could occure while the
    installation.
    """

    def print_readme(self, readme):
        print("{} - install: readme:".format(self.plugin))
        print("-"*50)
        BaseInstaller.print_readme(self, readme)
        print("-"*50)
        return None

    def install(self):
        print("{} - install: ...".format(self.plugin))
        
        try:
            BaseInstaller.install(self)
        except InstallError as error:
            print("{} - install: failure: {}".format(self.plugin, error))
        else:
            print("{} - install: Done.".format(self.plugin))
        return None

    
class Uninstaller(BaseUnInstaller):
    """
    Note: This uninstaller can only remove the *known* paths of the plugin.
    """
    
    def uninstall_directories(self):
        """
        Opens a command line dialog where the user can select which
        paths should be removed and removes them.
        """
        print("{} - uninstall: "\
              "\n\t This script can only remove the paths of the plugin"\
              "\n\t managed by the application. If the plugin used other"\
              "\n\t paths, you'll have to remove them manually."\
              .format(self.plugin))

        # Make for each path sure that it should be removed.
        paths = self.get_plugin_related_paths()
        for type_ in paths:
            path = paths[type_]
            if not os.path.exists(path):
                continue
            # Make sure, that the path should be # removed.
            question = "{} - uninstall: do you want to remove the {}? "\
                       .format(self.plugin, type_)
            if not userinput.ask(question):
                continue
            # Remove the path.
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except (OSError, PermissionError) as error:
                print("{} - uninstall: failure: the {} could not be removed: {}"\
                      .format(self.plugin, type_, error))
            else:
                print("{} - uninstall: the {} has been removed."\
                      .format(self.plugin, type_))

        # Call the uninstall method of the plugin if its loaded and
        # notify the user that the plugin might generate data at the
        # finish phase.
        plugin_manager = self.application.plugin_manager
        if plugin_manager.plugin_is_available(self.plugin):
            plugin_obj = plugin_manager.get_plugin(self.plugin)
            plugin_obj.uninstall()
            print("{} - remove: "\
                  "\n\t The plugin is loaded, therefore it is possible,"\
                  "\n\t that it creates data at the finish-phase of this "\
                  "\n\t application. To make sure that all paths have been"\
                  "\n\t removed, call this plugin again."\
                  .format(self.plugin))
        return None

    def uninstall_configuration(self):
        """
        Removes the configuration of the plugin.
        """
        conf = self.application.configuration.main
        question = "{} - uninstall: Do you want to remove the configuration?"\
                   .format(self.plugin)
        if self.plugin in conf and userinput.ask(question):
            conf.remove_section(self.plugin)
        return None

    def uninstall(self):
        """
        Removes the whole plugin.
        """
        self.uninstall_directories()
        self.uninstall_configuration()
        return None
    
    
class Plugins(BasePlugin):
    """
    Provides methods to install or remove plugins for this application.
    """

    version = "1.0.0"
    
    def __init__(self, application, name):
        BasePlugin.__init__(self, application, name)
        return None

    def setup_argparser_argument_group(self, group):
        group.title = self.name
        group.description = "This plugin provides methods to install or "\
                            "remove plugins of this application."
        
        group.add_argument(
            "--install",
            action = "store",
            dest = "install",
            metavar = "ARCHIVE",
            help = "Installs the plugin from the archive."
            )
        group.add_argument(
            "--uninstall",
            action = "store",
            dest = "uninstall",
            metavar = "PLUGIN",
            help = "Opens a dialog to remove the files and directories "\
            "of the plugin."
            )
        return None

    def run(self, args):
        if args.install:
            installer = Installer(self.application, args.install)
            installer.install()
            
        if args.uninstall:
            uninstaller = Uninstaller(self.application, args.uninstall)
            uninstaller.uninstall()
        return None
