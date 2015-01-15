Uninstallation
==============

.. attention:: 
   
   Before you uninstall the EMSM, please make sure, that you have at least
   a backup of the :file:`worlds` folder if you don't want to loose all of
   your worlds.

#. First of all, stop all worlds:
   
   .. code-block:: bash
      
      $ minecraft -W worlds --force-stop
      
#. Remove the EMSM directory:

   .. code-block:: bash
      
      $ rm -rf /opt/minecraft
   
#. Remove the user created during the installation:

   .. code-block:: bash

      $ deluser minecraft
      $ delgroup minecraft
   
#. Remove the :file:`/usr/bin/minecraft` link:

   .. code-block:: bash

      $ rm /usr/bin/minecraft
   
#. Uninstall the InitD service:

   .. code-block:: bash
   
      $ update-rc.d -f minecraft remove
      $ rm /etc/init.d/minecraft
      
#. You may have created some cron tabs, don't forget to delete them.