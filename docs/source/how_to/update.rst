Update
======

EMSM
----

.. note::
   
   The EMSM will deny the initialisation of a plugin if it's outdated. You can
   check the logfiles to see which plugins are outdated.
   
#. Check, if you already have the latest version:

   .. code-block:: bash
   
      $ minecraft --version
      EMSM x.x.x-gamma
   
#. Stop all minecraft worlds:

   .. code-block:: bash
   
      $ minecraft -W worlds --stop

#. Download the latest version of the EMSM and extract it in a temporary
   directory:
   
   .. code-block:: bash

      $ wget http://git.io/DPH_mg -O /tmp/emsm.tar.gz
      $ tar -xzf /tmp/emsm.tar.gz -C /tmp/
   
#. Overwrite the old :file:`emsm` and :file:`plugins` scripts. Make sure that
   you type the * at the end of the backslashes:
   
   .. code-block:: bash
      
      $ rm -r /home/minecraft/emsm
      $ cp -r /tmp/emsm-master/emsm/ /home/minecraft/
      $ cp -r -u /tmp/emsm-master/plugins/* /home/minecraft/plugins/
      
#. Make sure, that the EMSM user has **rw-access** to its directories after the 
   update:
   
   .. code-block:: bash

      $ chown -R minecraft:minecraft /home/minecraft
      
#. Invoke the script with no arguments to see if everything works:

   .. code-block:: bash

      $ minecraft
      
   When you get an error, a look in the CHANGELOG might be helpful.

Plugins
-------

.. hint:: 

   You should take a look into the documentation of a plugin **before** you
   update it.

These are your options to update a plugin:

* replace the source file and the library manually.
* use the :mod:`package manager <plugins>`