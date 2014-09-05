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
   
      $ minecraft -W worlds --force-stop

#. Download the latest version of the EMSM and extract it in a temporary
   directory:
   
   .. code-block:: bash

      $ wget http://git.io/DPH_mg -O /tmp/emsm-master.tar.gz
      $ tar -xzf /tmp/emsm-master.tar.gz -C /tmp/
   
#. Overwrite the old :file:`emsm` and :file:`plugin` scripts. Make sure that
   you type the * at the end of the backslashes:
   
   .. code-block:: bash
      
      $ rm -r /opt/minecraft/emsm
      $ cp -r /tmp/emsm-master/emsm/ /opt/minecraft/
      $ cp -r -u /tmp/emsm-master/plugins/* /opt/minecraft/plugins/
      
#. Make sure, that the EMSM user has **rw-access** to its directories after the 
   update:
   
   .. code-block:: bash

      $ chown -R minecraft:minecraft /opt/minecraft
      
#. Call the EMSM with a passive command to see if everyting worked fine:

   .. code-block:: bash

      $ minecraft plugins --list

Plugins
-------

.. hint:: 

   You should take a look into the documentation of a plugin **before** you
   update it.
   
The core plugins are automatically included in the current EMSM version and don't
need to be updated manually.

To update a third-party plugin, these are your options:

* replace the source file and the library manually.
* use the :mod:`package manager <plugins>`