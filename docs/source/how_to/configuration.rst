.. _configuration:

Configuration
=============

The :file:`conf/` directory contains all configuration files.

main.conf
---------

The :file:`main.conf` file contains the configuration of the EMSM and the
plugins.

.. code-block:: ini

    [emsm]

    # User that should run all of your minecraft worlds.
    user = minecraft

    # Maximum time that is waited until another EMSM instance releases
    # the file lock.
    # A negative values means no timeout and wait endless if necessairy.
    timeout = -1

    # You can provide a *screenrc* file. Please note, that it must be an
    # **absolute** path.
    # This option is optional.
    #
    #screenrc = /opt/minecraft/conf/screenrc
    screenrc =

Each plugin has its own section. E.g.:

.. code-block:: ini

    [backups]
    archive_format = bztar
    restore_message = This world is about to be resetted to an earlier state.
    restore_delay = 5
    max_storage_size = 30
    exclude_paths = logs
        mods

Some plugins allow you to override global options for each world. Please take
a look at the documentation of the :ref:`plugins` for further information.

server.conf
-----------

The :file:`server.conf` allows you to adjust some properties of the internal
EMSM server wrapper classes. Usually, it should not be necessairy to edit this
configuration file, but some times you have to.

Examples
''''''''

*   You want to adjust the java heap size:

    .. code-block:: ini

        [vanilla 1.8]
        # You can use these placeholders in the start_command:
        # * {server_exe}
        # * {server_dir}
        start_command = java -Xmx3G -jar {server_exe}

*   You want to use the latest server version, but the EMSM contains an old
    url:

    .. code-block:: ini

        [vanilla 1.8]
        url = https://...

    Make sure to update the server after changing the configuration:

    .. code-block:: bash

        $ minecraft -s "vanilla 1.8" server --update

You can override some options for each world, like the *start_command*.
This can be used to grant different worlds different amounts of memory.
You will learn how to do this in the next section.

\*.world.conf
-------------

.. note::

    This is only the EMSM configuration for the world. You still have to
    edit the :file:`server.properties` file in the world's directory.

Each world managed by the EMSM has its own configuration :file:`.world.conf`
file in :file:`conf/`. We will now add the world *morpheus*:

.. code-block:: bash

    $ # In the conf/ directory:
    $ touch morpheus.world.conf

This file is empty at the moment. On the next run of the EMSM, it will detect
the configuration file and fill it with default values:

.. code-block:: bash

    $ minecraft -W worlds --status

When you look into :file:`morpheus.world.conf`, you can find the *world*
section:

.. code-block:: ini

    [world]
    stop_timeout = 10
    stop_message = The world is going to be stopped.
    stop_delay = 10
    server = vanilla 1.10

*   **stop_timeout**

    The maximum time, waited until the world stopped after sending the
    ``stop`` command.

*   **stop_message**

    This message is printed before sending the stop command to the world.

*   **stop_delay**

    The time between the sending the *stop_message* and the *stop* command.
    If **stop_delay** and **stop_timeout** are both ``10``, the stop takes
    at least 10 seconds and at maximum 20.

*   **server**

    The name of the minecraft server that should power this world.

    Run ``minecraft server --list`` to get a list of all supported minecraft
    server. If your server is not listed, you can create a new plugin, which
    provides a :class:`server wrapper <emsm.core.server.BaseServerWrapper>`.

You can overridde some global plugin and server options for each world:

.. code-block:: ini

    [server:vanilla 1.10]
    start_command = java -Xmx1G -jar {server_exe} nogui

    [plugin:backups]
    max_storage_size = 10
    exclude_paths = logs
        mods

The configuration section for a server is the server name, prefixed with
``server:`` and the section for a plugin is the plugin's name, prefixed with
``plugin:``.

Please note, that you only overridde the configuration for a *specific* server,
not the current server of the world:

.. code-block:: ini

    # Has no effect, because the world is configured to use "vanilla 1.10",
    # and not "bungeecord".
    [server:bungeecord]
    start_command = echo "Hallo"

Check out the :ref:`plugins` documentation, if you want to know more about their
configuration.

Example
'''''''

.. code-block:: ini

    # This configuration file contains the configuration for the world
    #
    #     **morpheus**
    #
    # This file can be used to override global configuration values in
    # the *server.conf* and *emsm.conf* configuration files.
    #
    # [world]
    # stop_timeout = int
    # stop_message = string
    # stop_delay = int
    # server = a server in server.conf
    #
    # Custom options for the backups plugin:
    #
    # [plugin:backups]
    # archive_format = bztar
    # max_storage_size = 30
    #
    # Custom options for the vanilla 1.8 server:
    #
    # [server:vanilla 1.8]
    # start_command = java -Xms512m -Xmx1G -jar {server_exe} nogui
    #

    [world]
    stop_timeout = 10
    stop_delay = 5
    stop_message = The server is going down.
    	Hope to see you soon.
    server = vanilla 1.10

    [plugin:backups]
    max_storage_size = 10
    archive_format = zip
    exclude_paths = logs
    	mods
    	crash-reports

    [plugin:initd]
    enable = yes
