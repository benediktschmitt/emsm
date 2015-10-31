Installation
============

#.  Update the system packages:

    .. code-block:: bash

        $ sudo apt-get update
        $ sudo apt-get upgrade

#.  Install the depencies:

    .. code-block:: bash

        $ sudo apt-get install python3 python3-pip screen openjdk-7-jre-headless

    Note, that the EMSM needs at least **Python 3.2** to run.

#.  Install the EMSM Python package from PyPi:

    .. code-block:: bash

        $ sudo pip3 install --pre emsm

    This will also install all EMSM Python depencies.

#.  Create the user, that should run the EMSM:

    .. code-block:: bash

        $ sudo addgroup --system --no-create-home --disabled-login --group minecraft
        $ sudo adduser --system --no-create-home --disabled-login --ingroup minecraft minecraft

#.  Create the instance folder. This folder will later contain all worlds and
    server executables:

    .. code-block:: bash

        $ sudo mkdir /opt/minecraft

#.  Create the :file:`/opt/minecraft/minecraft.py` EMSM launcher and add it to
    the global PATH:

    .. code-block:: python3

        #!/usr/bin/env python3

        #/opt/minecraft/minecraft.py

        import emsm

        # Make sure, the instance dir is correct.
        emsm.run(instance_dir="/opt/minecraft")

    .. code-block:: bash

        $ sudo chmod +x /opt/minecraft/minecraft.py
        $ sudo ln -s /opt/minecraft/minecraft.py /usr/bin/minecraft

#.  Make sure the :file:`/opt/minecraft/` directory is owned by the minecraft
    user:

    .. code-block:: bash

        $ sudo chown -R minecraft:minecraft /opt/minecraft

#.  Execute the EMSM:

    .. code-block:: bash

        $ sudo minecraft emsm --version

#.  That's it. Your instance directory should now look like this:

    .. code-block:: none

        |- /opt/minecraft
            |- conf
            |- logs
            |- minecraft.py
            |- plugins
            |- plugins_data
            |- server
            |- worlds

You probably want to use some plugins like the :mod:`~emsm.plugins.guard`,
:mod:`~emsm.plugins.initd` or :mod:`~emsm.plugins.backups` plugin. So don't
forget to take a look at their documentation later.

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
