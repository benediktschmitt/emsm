EMSM
====

The **Extendable Minecraft Server Manager** (EMSM) is a minecraft server wrapper that is able to handle multiple minecraft worlds and server versions.

The **EMSM** itself provides only a simple but sufficient **API** to manage the worlds. The rest of the work is done by the plugins.

Online Documentation
====================

Please read the `online documentation <http://emsm.benediktschmitt.de`_ for a full introduction in the **EMSM**. The documentation is small and comprehensible.

Quick Installation
==================

Environment
-----------

#. Install the depencies:

   * Python3.2 or higher
   * Java 6 or higher
   * Screen
   
   ::
   
      apt-get update 
      apt-get install screen openjdk-7-jre-headless python3.2
      
#. Create the user that should run the application::

      adduser minecraft --disabled-password --shell=/bin/false
      
#. Switch to the user and its home directory::

      su minecraft
      cd ~/
      
#. Download the application and extract it::

      wget https://link_to_the_app -O /tmp/emsm.tar.bz2
      tar -xjf /tmp/emsm.tar.bz2
      
#. Copy the :file:`bin_script` in the :file:`/usr/build` directory::
   
      cp emsm/bin_script /usr/bin/minecraft

   Now, you can invoke the application with::
   
      minecraft --arg1 --arg2

#. Well, that's all. For the first run, type::

      minecraft       

Configuration
-------------

main.conf:

.. code-block:: ini

   [emsm]
   user = minecraft
   
server.conf:

.. code-block:: ini

   [vanilla_1.6]
   server = minecraft_server_1.6.jar
   url = https://s3.amazonaws.com/Minecraft.Download/versions/1.6.2/minecraft_server.1.6.2.exe
   start_args = nogui.
   
worlds.conf:

   [foo]
   port = 25565
   server = vanilla_1.6
   
  
First run
---------

To perfom a dry-run, type::

   minecraft
   
If you need more help, use the **--help** argument::

   minecraft -h
   minecraft -h -p worlds
   minecraft -h -p server
   minecraft -h -p backups
   minecraft -h -p ...
   
Versioning
==========

The **EMSM** uses semantic version numbers. Take a look at http://semver.org/ for further information.