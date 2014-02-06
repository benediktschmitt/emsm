:mod:`server`
=============

.. module:: server

About
-----

This plugin provides a user interface for the server wrapper. It can handle
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

.. code-block:: ini

   [server]
   update_message = The server is going down for an update.

**update_message**
   
   Is a string, printed before stopping a world for an update.

Arguments
---------
   
Select the server with the *common* arguments **--server** or **--all-server**.

.. option:: --configuration
   
   Prints the configuration of the server.
   
.. option:: --update

   Updates the server. Tries a normal stop of all worlds, that are running this
   server. If the stop fails, the update will be aborted.
   
.. option:: --force-update

   Forces the update of the server by forcing the stop of all worlds, that are
   running the server.
   
.. option:: --uninstall

   Removes the server.
   
   .. hint:: 

      Using this argument is strongly **recommended** if you want to remove a 
      server from the application. Removing a server with this command
      makes sure, that no world is still running the server and that the 
      configuration files keep in a consistent state.