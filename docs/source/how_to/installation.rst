Installation
============

.. sidebar:: Download

   http://git.io/DPH_mg
 
Manual installation
-------------------
   
#. The EMSM requires *Python 3.2* or higher and *screen*, we need *java* to 
   run the minecraft server, *tar* to extract the EMSM archive and *wget* 
   to download it:
   
   .. code-block:: bash
   
      $ apt-get update
      $ apt-get install screen openjdk-7-jre-headless python3
      
#. Create the user that should run the application:

   .. code-block:: bash

      $ adduser minecraft --disabled-password --shell=/bin/false
      
#. Switch to the home directory of *minecraft*:
   
   .. code-block:: bash
   
      $ cd /home/minecraft
      
#. Download the application and extract it in the home directory of *minecraft*:

   .. code-block:: bash

      $ wget https://github.com/benediktschmitt/emsm/archive/master.tar.gz
      $ tar -xzf master.tar.gz
      $ mv emsm-master/* ./
      $ rm -r emsm-master master.tar.gz
      $ chown -R minecraft:minecraft /home/minecraft 
      
#. Copy the :file:`bin_script` into the :file:`/usr/bin` directory and make it
   executable:
   
   .. code-block:: bash
   
      $ cp emsm/bin_script.sh /usr/bin/minecraft
      $ chmod +x /usr/bin/minecraft
      
#. Copy the :file:`initd_script` into the :file:`/etc/init.d` folder:

   .. code-block:: bash
   
      $ cp emsm/initd_script.sh /etc/init.d/minecraft
      $ chmod +x /etc/init.d/minecraft
      $ update-rc.d minecraft defaults

#. Well, that's all. For the first run, type:

   .. code-block:: bash

      $ minecraft 
      
   This will create the other subdirectories and the configuration files. If 
   the :file:`bin-script` does not work, take a look at the next section.
       
Known issues
------------

Running EMSM under another user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you run the application under another user than *minecraft*, you
have to edit the :file:`main.conf` configuration file:
   
.. code-block:: ini

   [emsm]
   user = foobar

Furthermore, you have to edit the :file:`bin_script` as described in the 
next section.

The *bin_script* does not work
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You probably have to adapt the ``USER`` and ``LOCATION`` variable:

.. code-block:: bash

   #!/bin/bash

   # The user that should run your minecraft worlds.
   USER=minecraft

   # The root directory of the EMSM. This directory contains the *emsm* directory.
   LOCATION=/home/$USER

   # ...
   
If the script still does not work, please report it on 
:ref:`GitHub <contribute>` and use

.. code-block:: bash

      $ python3 /home/minecraft/emsm/application.py 
   
to invoke the EMSM until the bug is fixed.
