![emsm_logo](http://emsm.readthedocs.org/en/latest/_static/emsm_48x48.png)

# EMSM
The **Extendable Minecraft Server Manager** (EMSM) handles
**multiple minecraft worlds** and **server versions**. The application is 
completely written in Python.

The **EMSM** provides a simple, but sufficient **CLI** (*command line interface*)
to manage world and server tasks.
It is based on plugins therefore easily expandable.

The separation of Minecraft worlds and server executables allows to easily
manage several different versions of servers (e.g. Vanilla and Bukkit in 
multiple versions) for different worlds. The **EMSM** comes with a backup 
mechanism as one of the core plugins, which can be automated to create
periodical backups. It also provides a core plugin to check the availability 
of the server and restart them if its configured to do so. Another plugin aims 
at integrating **EMSM** with *init.d* to start/stop the server on
(re-)boot/shutdown processes.


## Get started
Please read the [online documentation](http://emsm.readthedocs.org) for 
a full introduction. I tried to keep it simple and short. The EMSM will
be installed in less than 10 minutes.


## Contribution and New Plugins
If you have a good idea for a new plugin, 
[let us know](https://github.com/benediktschmitt/emsm/issues) :).

When you found a bug, please report it. 


## Versioning
The **EMSM** uses semantic version numbers. Take a look at http://semver.org/
for further information.


## License
* 0.0.0-beta - 2.0.0-beta: [GNU GPL v3](https://www.gnu.org/copyleft/gpl.html)
* 2.0.1-beta - current release: [MIT License](LICENSE).
