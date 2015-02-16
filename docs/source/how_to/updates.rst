Updates
=======

From time to time, the EMSM receives some updates. Especially the server
database and the server download urls. So how can you update the EMSM?

Server updates
--------------

The server software is usually updated faster than the EMSM database.
But don't worry, you can often use the latest server software with the EMSM.

Let's assume, the *minecraft server 1.8* received a patch from mojang and you
want to use it:

#.  Edit the :file:`server.conf` configuration file:

   .. code-block:: ini

        [vanilla 1.8]
        # Setting the url here, will overwrite the value in the EMSM database.
        url = https://s3.amazonaws.com/Minecraft.Download/versions/1.8.1/minecraft_server.1.8.1.jar

#.  Update the server with the :mod:`~emsm.plugins.server` plugin:

    .. code-block:: bash

        $ minecraft -s "vanilla 1.8" server --update

If the update fails, the old server software will be restored and nothing
changed.

Please take a look at the :ref:`server configuration <configuration>` and the
:mod:`~emsm.plugins.server` plugin for more information.

EMSM updates
------------

The EMSM is a Python package and you can simply update it using *pip*:

.. code-block:: bash

    $ pip3 install --upgrade emsm

Since the instance folder is not touched by this command, there is no need for
a backup before an update anymore.

If the EMSM does not work as expected after the update, take a look at the
:ref:`changelog` or create an
`issue <https://github.com/benediktschmitt/emsm/issues>`_.
