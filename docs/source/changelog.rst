.. _changelog:

Changelog
=========

This log contains only the changes beginning with version *3.1.1-beta*.

*   4.0.0-beta

    *   **changed** The EMSM is now a valid Python package available via PyPi.
    *   **cleaned** the documentation
    *   EMSM upgrade from version 3 beta:

        #.  Install the EMSM package

            .. code-block:: bash

                # I encourage you to use virtualenv!
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

                import os
                import emsm

                emsm.run(os.path.dirname(os.path.abspath(__file__)))

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
