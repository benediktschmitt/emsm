.. image:: https://raw.githubusercontent.com/benediktschmitt/emsm/master/docs/source/_static/logo/emsm_48x48.png
    :width: 16px
    :height: 16px
    :align: left

EMSM
====

The *Extendable Minecraft Server Manager* (EMSM) handles
**multiple minecraft worlds** and **server versions**. It is completly written
in Python and can be easily modified by the user.

The *EMSM* provides a simple, but powerful and extensive command line interface,
which allows to manage your minecraft server and automize tasks.

The separation of minecraft worlds and server executables allows to manage
several different versions of server (e.g. Vanilla and Bukkit in
multiple versions) for different worlds. The *EMSM* comes with a backup
mechanism as one of the core plugins, which can be automated to create
periodical backups. It also provides a plugin to check the availability
of the server and restart them, if its configured to do so. Another plugin aims
at integrating *EMSM* with *init.d* to start/stop the server on
(re-)boot/shutdown processes.

Get started
-----------

Please read the `online documentation <http://emsm.readthedocs.org>`_ for
a full introduction. I tried to keep it simple and short. The EMSM will
be installed in less than 10 minutes.

When you need help, don't hesitate to create an issue.

Contribution and New Plugins
----------------------------

If you have a good idea for a new plugin,
`let us know <https://github.com/benediktschmitt/emsm/issues>`_ :).

When you found a bug, please report it.

Versioning
----------

The *EMSM* uses semantic version numbers. Take a look at http://semver.org/
for further information.

License
-------

* 0.0.0-beta - 2.0.0-beta: `GNU GPL v3 <https://www.gnu.org/copyleft/gpl.html>`_
* 2.0.1-beta - current release: `MIT License <LICENSE.rst>`_.
