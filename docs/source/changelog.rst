.. _changelog:

Changelog
=========

This log contains only the changes beginning with version *3.1.1-beta*.

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
