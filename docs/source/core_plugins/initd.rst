:mod:`initd`
=====================

.. module:: initd

About
-----

Works as interface between the linux *initd service* and the EMSM.

Download
--------

You can find the latest version of this plugin in the EMSM  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Installation
------------

.. code-block:: bash

   $ cp emsm/initd_script /etc/init.d/minecraft
   $ chmod +x /etc/init.d/minecraft
   $ update-rc.d minecraft
   

Configuration
-------------

main.conf
^^^^^^^^^

.. code-block:: ini
   
   [initd]
   manage_all_worlds = no

**manage_all_worlds**

   If yes, all worlds are automatically started/stopped if the runlevel
   demands it.

worlds.conf
^^^^^^^^^^^

.. code-block:: ini

   [foo]
   enable_initd = no

**enable_initd**
   
   Is the local value for *manage_all_worlds*.
   
Arguments
---------

.. option:: --start

   Starts all worlds, where the *enable_initd* configuration value is true.

.. option:: --stop
   
   Stops all worlds, where the *enable_initd* configuration value is true.
   
Events
------

The plugin emits the corresponding events:

* initd_start()
* initd_stop()

Both with no argument.