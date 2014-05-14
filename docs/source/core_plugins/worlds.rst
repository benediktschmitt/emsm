:mod:`worlds`
=============

.. module:: worlds

About
-----

This plugin provides a user interface for the server wrapper. It handles
the server files and their configuration parameters easily.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Configuration
-------------

.. code-block:: ini

   [worlds]
   default_log_start = 0
   default_log_limit = 10
   open_console_delay = 1
   send_command_timeout = 10
   
**default_log_start**

   Is the first line of the log, that is printed. Can be overwritten by a
   command line argument.
   
**default_log_limit**

   Is the default number of log lines, that is printed at once. This
   value can be overwritten by a command line argument too.
   
**open_console_delay**

   Time between printing the WARNING and opening the console.

**send_command_timeout**

   Maximum time waited for the response of the minecraft server,
   if the *--verbose-send* command is used.
      
Arguments
---------

.. option:: --configuration
   
   Prints the section of the world in the :file:`worlds.conf`.
   
.. option:: --properties

   Prints the content of the :file:`server.properties` file.
   
.. option:: --log

   Prints the log.
   
.. option:: --log-start LINE

   The first line of the log that is printed. If *'-10'* (with quotes!), the 
   10th last line will be the first line that is printed.
   
.. option:: --log-limit LINES

   Limits the number of printed lines.
   
.. option:: --pid

   Prints the PID of the screen session that runs the server.
   
.. option:: --status

   Prints the status of the world (online or offline).
   
.. option:: --send CMD

   Sends the command to the world.
   
   .. note:: Escaping commands with **spaces**
   
      If you want to send a command like ``say Hello players!``, you have to
      escape it. Under Linux, this works:
      
      .. code-block:: bash
      
         minecraft -W worlds --send '"say Hello players!"'
   
.. option:: --verbose-send CMD

   Sends the command to the server and prints the echo in the logfiles.
   
.. option:: --console

   Opens the server console.
   
.. option:: --start

   Starts the world
   
.. option:: --stop

   .. warning::
   
      Stopping the world not using the dedicated commands, will **not** 
      call the **event dispatcher** and may cause bugs.
      
   Stops the world
   
.. option:: --force-stop

   Like --stop, but kill the processes if the world is still online
   after the smooth stop.   
   
.. option:: --kill

   .. warning::

      Using this command can cause data loss.
      
   Kills the process of the world.
   
.. option:: --restart
   
   Restarts the world. If the world is offline, the world will be started.
   
.. option:: --force-restart

   Like --restart, but forces the stop of the world if necessairy.
   
.. option:: --uninstall

   Removes the world and its configuration.
   
Examples
---------

.. code-block:: bash
   
   # Start all worlds:
   $ minecraft -W worlds --start
   
   # Send a command to the server and print the console output:
   $ minecraft -W worlds --verbose-send list
   $ minecraft -W worlds --verbose-send 'say Use more TNT!'
   
   # Print the log of the world *foo*:
   $ minecraft -w foo worlds --log
   $ minecraft -w foo worlds --log-start '-20'
   $ minecraft -w foo worlds --log-limit '5'
   $ minecraft -w foo worlds --log-start '-50' --log-limit 10
   
   # Open the console of a running world
   $ minecraft -w bar worlds --console
   
   ...