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

Each plugin has its own section. E.g.:

.. code-block:: ini

    [backups]
    archive_format = bztar
    restore_message = This world is about to be resetted to an earlier state.
    restore_delay = 5
    max_storage_size = 30
    include_server = yes

Please take a look at the documentation of the :ref:`plugins` for further
information.

server.conf
-----------

The :file:`server.conf` allows you to adjust some properties of the internal
EMSM server wrapper classes. Usually, it should not be necessairy to edit this
configuraiton file, but some times you have to.

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

worlds.conf
-----------

The worlds managed by the EMSM have to be declared in the :file:`worlds.conf`
configuration file. Each section represents another world.

The :file:`worlds.conf` configuration file contains only the EMSM configuration
for the worlds. You still have to edit the :file:`server.properties` file in
the world's directory.

.. code-block:: ini

    [the world's name]
    stop_timeout = 10
    stop_message = The world is going to be stopped.
    stop_delay = 10
    server = vanilla 1.8

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

Example
'''''''

.. code-block:: ini

    # This section contains the default values for all worlds.
    # It is not a real world.
    [DEFAULT]
    stop_delay = 5
    stop_timeout = 10
    stop_message = The server is going down.
        Hope to see you soon.
    server = vanilla 1.8

    [foo]
    # This ok, when all default values are set and valid.

    [bar]
    stop_delay = 0
    stop_timeout = 20
    stop_message = See you later aligator.
    server = vanilla 1.5

    [lobby]
    server = bungeecord

Some plugins like :mod:`~emsm.plugins.initd` provide additional configuration
options:

.. code-block:: ini

    [foo]
    # InitD has to be enabled for each world or once in the DEFAULT section.
    enable_initd = yes
