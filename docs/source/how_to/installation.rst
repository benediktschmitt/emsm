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
      $ apt-get install screen openjdk-7-jre-headless python3 python3-pip
      
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
      
#. The EMSM needs some PyPi packages like *blinker*, so install them:
 
   .. code-block:: bash
   
      $ pip-3.2 install -r emsm/requirements.txt

#. Create a link in :file:`/usr/bin/` so that you can call the EMSM easily from
   your command line:
   
   .. code-block:: bash
      
      $ ln -s /home/minecraft/minecraft.py /usr/bin
      $ chmod +x /usr/bin/minecraft
      
#. Copy the :file:`initd_script` into the :file:`/etc/init.d` folder:

   .. code-block:: bash
   
      $ cp emsm/initd_script.sh /etc/init.d/minecraft
      $ chmod +x /etc/init.d/minecraft
      $ update-rc.d minecraft defaults

#. Well, that's all. For the first run, type:

   .. code-block:: bash

      $ minecraft 
      
   This will create the other subdirectories and the configuration files.
       
Known issues
------------

Running EMSM under another user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you run the application under another user than *minecraft*, you
have to edit the :file:`conf/main.conf` configuration file before the first 
EMSM start:
   
.. code-block:: ini

   [emsm]
   user = foobar