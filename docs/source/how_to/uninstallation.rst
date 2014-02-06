Uninstallation
==============

.. attention:: 
   
   Before you uninstall the EMSM, please make sure, that you have at least
   a backup of the :file:`worlds` folder!

First of all, stop all worlds:
   
.. code-block:: bash
   
   $ minecraft -W worlds --force-stop
   
Remove the user created during the installation:

.. code-block:: bash

   $ deluser --remove-home minecraft
   
Remove the :file:`bin_script` and the :file:`initd_script`:

.. code-block:: bash

   $ rm /usr/bin/minecraft
   $ update-rc.d -f minecraft remove
   $ rm /etc/init.d/minecraft