![emsm_logo](http://benediktschmitt.de/docs/emsm/_static/logo/emsm_48x48.png)

# EMSM
The **Extendable Minecraft Server Manager** (EMSM) handles
**multiple minecraft worlds** and **server versions**. The application is 
completely written in Python.

The **EMSM** provides a simple, but sufficient **CLI** (*command line interface*)
to manage world and server tasks.
It is based on plugins therefore easily expandable. Further is the **EMSM** 
written in a modular manner, that allows to reuse single components independent 
of the rest of **EMSM** (if one wishes).

The separation of Minecraft worlds and server executables allows to easily
manage several different versions of servers (e.g. Vanilla and Bukkit in 
multiple versions) for different worlds. The **EMSM** comes with a backup 
mechanism as one of the core plugins, which can be automated to create
periodical backups. It also provides a core plugin to check the availability 
of the server and restart them if its configured to do so. Another plugin aims 
at integrating **EMSM** with *init.d* to start/stop the server on
(re-)boot/shutdown processes.


## Reference

* [Documentation](#documentation)
* [Installation](#installation)
* [Uninstallation](#uninstallation)
* [Directory structure](#directory-structure)
* [Contribution and New Plugins](#contribution-and-new-plugins)
* [Versioning](#versioning)
* [License](#license)


## Highlights
* backup management
* world guard
* init.d support
* World status reports


## Documentation
Please read the [online documentation](http://benediktschmitt.de/docs/emsm) for 
a full introduction. I tried to keep it simple and short. You'll come grips with
it in less than 10 minutes.


## Installation


### Environment
1. The **EMSM** requires *Python 3.2* or higher and *screen*. Furthermore, you
	need *java* to run the minecraft server, *tar* to extract the **EMSM** 
	archive and *wget* to download it. So let's start:

			$ apt-get update
			$ apt-get install screen openjdk-7-jre-headless python3 tar wget

2.	Create the user that should run the application and your minecraft server:

			$ adduser minecraft --disabled-password --shell=/bin/false

3.	Switch to the home directory of the *minecraft* user:

			$ cd /home/minecraft

4.	Download the latest master branch and extract it in the home directory
	of *minecraft*:

			$ wget https://github.com/benediktschmitt/emsm/archive/master.tar.gz
			$ tar -xzf master.tar.gz
			$ mv emsm-master/* ./
			$ rm -r emsm-master master.tar.gz
			$ chown -R minecraft:minecraft /home/minecraft

	The whole **EMSM** application is now installed in the home directory of the
	user *minecraft*.

5.	To invoke the **EMSM** easily from everywhere, symlink the *bin_script* into
	the */usr/bin* directory:

			$ ln -s /home/minecraft/emsm/bin_script.sh /usr/bin/minecraft

6.	**Optional**: You can copy the *initd_script* to use the features 
	of the *initd* plugin. This will start your worlds after reboot and stops
	them when your system is going down.

			$ cp emsm/initd_script.sh /etc/init.d/minecraft
			$ chmod +x /etc/init.d/minecraft
			$ update-rc.d minecraft defaults

7.	Well, that's all. For a dry run, you can use the worlds plugin without any
	parameter:

			$ minecraft worlds

	This should create the subdirectories and the configuration files. If the
	*bin_script* does not work, take a look at the complete
	[documentation](http://benediktschmitt.de/docs/emsm).

8.	**Optional**: You might want to consider adding cronjobs for backup or guard plugin in e.g. */etc/cron.d/emsm*
	```Shell
	# Runs the guard every 5 minutes for the world, where *enable_guard* is true:
	*/5 * *   *   *   root minecraft guard
	# Backup all worlds everyday at 6am
	0 6 * * * root test -x /usr/bin/minecraft && /usr/bin/minecraft -W backups --create
	```

	
### Configuration
* main.conf:

	```ini
	[emsm]
	user = minecraft
	```

* server.conf:

	```ini
	[vanilla_1.6]
	server = minecraft_server_1.6.jar
	# Try *http* if *https* does not work.
	url = http://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar
	start_args = nogui.
	```

* worlds.conf:

	```ini
	[foo]
	port = 25565
	server = vanilla_1.6
	```

	
### Finish
To start all worlds, use the command:

	$ minecraft -W worlds --start

If the minecraft server has not been downloaded yet, it will be downloaded now.


## Uninstallation

**Warning:** I suggest, that you make at least a backup of the *worlds* 
folder, before you remove the **EMSM**.

1. Stop all worlds:
	
		$ minecraft -W worlds --force-stop
		
2. Remove the user created during the installation:

		$ deluser --remove-home minecraft
	
3. Remove the *bin_* and the *initd_* script:

		$ rm /usr/bin/minecraft
		$ update-rc.d -f minecraft remove
		$ rm /etc/init.d/minecraft
	
That's all.


## Commands
There are some common arguments and run types you should know:

* The **dry-run**. Only the service routines will be called:

		$ minecraft

* The **help** argument:

		$ minecraft -h
		$ minecraft worlds -h
		$ minecraft server -h
		$ minecraft backups -h
		...
		
* The **doc view** of a plugin:

		$ minecraft plugins --doc [YOUR_PLUGIN]
		$ minecraft plugins --doc worlds
		

Each plugin provides its own arguments, similar to *git*. There are only a few
**global arguments** to unify the interface:

* Select all worlds:

		$ minecraft -W [plugin ...]
		$ minecraft --all-worlds [plugin ...]

* Select single worlds:

		$ minecraft -w foo -w bar [plugin ...]
		$ minecraft --world foo --world bar [plugin ...]

* Select all server software:

		$ minecraft -S [plugin ...]
		$ minecraft --all-server [plugin ...]

* Select only a few server:

		$ minecraft -s vanilla -s bukkit [plugin ...]
		$ minecraft --server vanilla --server bukkit [plugin ...]


## Directory structure
The **EMSM** comes with the following directories:

* **configuration**:
	contains all configuration files
* **emsm**:
	contains all executable source files of the **EMSM** application.
* **plugins**:
	contains all executable source files of the plugins.
* **plugins_data**:
	contains the data used or produced by the plugins.
* **server**:
	contains the executables of the server files.
* **worlds**:
	contains the data of the minecraft worlds.


## Contribution and New Plugins
If you have a good idea for a new plugin, let me know :)

Please consider also to contribute to the code. When you found a bug, please
report it and/or try to fix it.


## Versioning
The **EMSM** uses semantic version numbers. Take a look at http://semver.org/
for further information.


## License
* 0.0.0-beta - 2.0.0-beta: [GNU GPL v3](https://www.gnu.org/copyleft/gpl.html)
* 2.0.1-beta - current release: [MIT License](LICENSE).
