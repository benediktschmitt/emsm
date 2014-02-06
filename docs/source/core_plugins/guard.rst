:mod:`guard`
=====================

.. module:: guard

About
-----

Controls each time the **EMSM** is invoked if the worlds are running and 
reachable from outside.

Download
--------

You can find the latest version of this plugin in the EMSM  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

main.conf
^^^^^^^^^

.. code-block:: ini

   [max_rows]
   error_action = none
   error_regex = (\[SEVERE\])
   auto_run = no
   guard_all_worlds = no
   
**error_action**

   Defines the reaction on a detected error.
   
   * *none*     Do nothing
   * *restart*  Try to restart the world
   * *stop*     Try to stop the world.
   * *stderr*   Print a message to stderr
    
**error_regex**

   If this regex matches the log file, it caues an error handling.
   
**auto_run**

   If yes, run each time, the EMSM is invoked.
   
**guard_all_worlds**

   If yes, this plugin guards all worlds per default.      
      
worlds.conf
^^^^^^^^^^^

.. code-block:: ini

   [foo]
   enable_guard = no
   
**enable_guard**
   
   Enables the guard for this plugin. Overwrites the global
   flag *guard_all_worlds*.

Summary
^^^^^^^
If you want to enable the plugin for almost all worlds, use the *enable_guard* 
option in the *DEFAULT* section:

.. code-block:: ini

   [DEFAULT]
   enable_guard = yes
   
   [foo]
   # This world is protected.
   
   [bar]
   # This world is not protected.
   enable_guard = no   

Arguments
---------

The guard has no arguments. If invoked it simply runs the guard for ALL worlds 
selected with the global *-W* or *-w* argument AND the worlds where 
*enable_guard* is true. 
   
Cron
----

This plugin is made for *cron*:

.. code-block:: text

   # m h dom mon dow user command
   # Runs the guard every 5 minutes for all worlds
   */5 * *   *   *   root minecraft -W guard
   
   # Runs the guard every 5 minutes for the world, where *enable_guard* is true:
   */5 * *   *   *   root minecraft guard
   