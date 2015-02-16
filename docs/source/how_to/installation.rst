Installation
============

#.  Download the install script:

    **Debian:**

    .. code-block:: bash

        $ wget https://foobar -O /tmp/emsm_installer

    **RedHat:**

    .. code-block:: bash

        $ wget https://foobar -O /tmp/emsm_installer

#.  Run the installer:

    .. code-block:: bash

        $ bash /tmp/emsm_installer

#.  Execute the EMSM:

    .. code-block:: bash

        $ minecraft plugins --list

#.  That's it. Your instance directory should now look like this:

    .. code-block:: none

        |- (/opt/minecraft)
            |- conf
            |- logs
            |- minecraft.py
            |- plugins
            |- plugins_data
            |- server
            |- worlds

Troubleshooting
---------------

WrongUserError
^^^^^^^^^^^^^^

If you run the application under another user than *minecraft*, you
have to edit the :file:`conf/main.conf` configuration file before you call the
EMSM the first time otherwise you will get a ``WrongUserError``:

.. code-block:: ini

    [emsm]
    user = foobar
