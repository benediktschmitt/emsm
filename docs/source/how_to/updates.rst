Updates
=======

From time to time, the EMSM receives some updates. Especially the server 
database and the server download urls. So how can you update the EMSM?


Server updates
--------------

The server software is usually updated faster than the EMSM database.
But don't worry, you can often use the latest server software with the EMSM.

Let's assume, the *minecraft server 1.8* received an update from mojang and
you want to update the server:

1. Edit the ``server.conf`` configuration file:

   .. code-block:: ini
   
      [vanilla 1.8]
      # Setting the url here, will overwrite the value in the EMSM database.
      url = https://s3.amazonaws.com/Minecraft.Download/versions/1.8.1/minecraft_server.1.8.1.jar
      
2. Reinstall the server software using the :mod:`~plugins.server` plugin:

   .. code-block:: bash
   
      $ minecraft -s "vanilla 1.8" server --reinstall
   
If the reinstallation fails, the old server software will be restored and 
nothing has changed.

Please take a look at the :ref:`server configuration <configuration>` and the 
:mod:`~plugins.server` plugin for more information.


EMSM updates
------------

.. hint::

   Before you update the EMSM, please create a temporary copy of the whole
   EMSM folder. Something can go always wrong.

You can update the EMSM either *manually* or using *git*.

Before we start, check if your local version is out of date:

.. code-block:: bash
  
   $ minecraft emsm --check-update
   3.1.1-beta
   
Note, that it is possible that new plugins have been added to the EMSM during 
the last patches. If your EMSM folder already contains files with the same
names, you have to rename them.


Git update
^^^^^^^^^^

The EMSM git repository is configured to ignore all instance folders. Only 
EMSM files and core plugins are indexed. So you can use the ``git pull`` 
command to update all EMSM files without overwriting local changes.

#. Stop all worlds:

   .. code-block:: bash
   
      $ minecraft -W worlds --force-stop
      
#. Switch to the minecraft user (to avoid running git as root):

   .. code-block:: bash
   
      su minecraft --shell=/bin/bash
      
#. Change to the EMSM root folder and pull any changes from our GitHub 
   repository:
   
   .. code-block:: bash
   
      $ cd /opt/minecraft
      $ git pull origin
      
#. Exit the *minecraft* user shell:

   .. code-block:: bash
   
      $ exit

      
Manual update
^^^^^^^^^^^^^

The manual update is basically a simplified new installation of the EMSM.

#. Stop all worlds:

   .. code-block:: bash
      
      $ minecraft -W worlds --force-stop
      
#. Download the latest EMSM repository to a temporary directory and extract
   it:

   .. code-block:: bash
   
      $ wget https://github.com/benediktschmitt/emsm/archive/master.tar.gz -O /tmp/emsm-master.tar.gz
      $ tar -xzf /tmp/emsm-master.tar.gz -C /tmp
      
2. Remove all *non*-instance folders and replace them with the new ones:

   .. code-block:: bash
   
      $ rm -r /opt/minecraft/docs
      $ rm -r /opt/minecraft/emsm
      $ cp -ru /tmp/emsm-master/* /opt/minecraft

3. Make sure the *minecraft* user owns the folder:

   .. code-block:: bash
      
      $ chown -R minecraft:minecraft /opt/minecraft
      
That's it. Please check the :ref:`changelog` for new depencies or other
major changes. You will have to apply them manually or as described in the
:ref:`changelog`.