.. _changelog:

Changelog
=========

This log contains only the changes beginning with version *3.1.1-beta*.

*   5.0.0-beta

    *   The :file:`worlds.conf` configuration file has been replaced with a
        configuration file for each world.

        Upgrading is easy: For each world in :file:`worlds.conf`, create a
        configuration file :file:`name.world.conf` in the configuration
        directory:

        The *morpheus* section in :file:`worlds.conf`:

        .. code-block:: ini

            [morpheus]
            server = vanilla 1.11
            enable_initd = yes
            stop_timeout = 10

        becomes the :file:`morpheus.world.conf` configuration file, with the
        content:

        .. code-block:: ini

            [world]
            server = vanilla 1.11
            stop_timeout = 10

            [plugin:initd]
            enable = yes

    *   Custom plugins still work, if you update the ``VERSION``
        attribute.

    *   **changed** The *enable_initd* option has been replaced with a new
        option *enable* in the ``plugin:initd`` configuration section
        (checkout the documentation of the :mod:`~emsm.plugins.initd` plugin
        for more information).

    *   **added** You can now overridde the server *start_command* for each
        world.

    *   **added** The :mod:`~emsm.plugins.backups` plugin has now an *exclude*
        options, which allows you to exclude world directories from the backup.
        (`issue #58 <https://github.com/benediktschmitt/emsm/issues/58>`_)

    *   **added** Some *backups* options can be overridden for each world.

    *   **added** :meth:`emsm.core.base_plugin.BasePlugin.world_conf`
    *   **added** :meth:`emsm.core.base_plugin.BasePlugin.global_conf`
    *   **deprecated** :meth:`emsm.core.base_plugin.BasePlugin.conf`,
        use :meth:`global_conf` instead.

*   4.0.13-beta

    *   **fixed** The start command option ``nogui`` of the forge server

*   4.0.12-beta

    *   **fixed** `issue #35 <https://github.com/benediktschmitt/emsm/issues/35>`_
    *   **fixed** The start command option ``nogui`` of the vanilla server

*   4.0.5-beta

    *   The server executables are now always placed in a subdirectory of
        ``INSTANCE_ROOT/server/``.
    *   **removed** :meth:`emsm.core.server.BaseServerWrapper.server`
    *   **added**   :meth:`emsm.core.server.BaseServerWrapper.directory`
    *   **added**   :meth:`emsm.core.server.BaseServerWrapper.exe_path`
    *   The *start_command* in the :file:`server.conf` accepts due to the
        changes above now these placeholders:

        *   ``{server_exe}``    Points to the server executable
        *   ``{server_dir}``    Points to the directory which contains all
            server software.
    *   *added**    :meth:`emsm.core.paths.Pathsystem.server_`

*   4.0.0-beta

    *   **changed** The EMSM is now a valid Python package available via PyPi.
    *   **cleaned** the documentation
    *   EMSM upgrade from version 3 beta:

        #.  Install the EMSM package

            .. code-block:: bash

                $ sudo pip3 install emsm

        #.  Remove obsolete folders and files:

            .. code-block:: bash

                $ rm README.md
                $ rm LICENSE.md
                $ rm minecraft.py
                $ rm .gitignore

                $ rm -rf .git/
                $ rm -rf docs/
                $ rm -rf emsm

                # You probably want to keep your own plugins. So modify the
                # command to delete only the EMSM plugins (worlds, server, ...).
                $ rm -r plugins/*

        #.  Create the :file:`minecraft.py` file:

            .. code-block:: python

                #!/usr/bin/env python3

                import emsm

                # Make sure, the instance folder is correct.
                emsm.run(instance_dir = "/opt/minecraft")

            .. code-block:: bash

                $ chmod +x /opt/minecraft/minecraft.py
                $ chown minecraft:minecraft /opt/minecraft/minecraft.py

*   3.1.1-beta

    *   **added**   :meth:`emsm.core.server.BaseServerWrapper.world_address` method
    *   **added**   :meth:`emsm.core.server.BaseServerWrapper.log_error_re` method
    *   **added**   *termcolor* as Python requirement
    *   **added**   *colorama* as Python requirement
    *   **added**   *pyyaml* as Python requirement
    *   **added**   *wait_check_time* parameter to
        :meth:`emsm.core.worlds.WorldWrapper.start`
    *   **updated** the console output: the output is now sorted, colored and
        consistent
    *   **updated** :mod:`emsm.plugins.guard` plugin (big rework, take a look)
