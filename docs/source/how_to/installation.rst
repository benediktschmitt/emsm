Installation
============

.. sidebar:: Download

   http://git.io/DPH_mg
 
Manual installation
-------------------

#. Update your system packages:

   .. code-block:: bash
   
      $ apt-get update
      $ apt-get upgrade
      
#. Install the depencies:
 
   .. code-block:: bash
   
      $ apt-get install screen openjdk-7-jre-headless python3 python3-pip
      
   Note, that the EMSM requires at least *Python 3.2* to run.
   
#. Install the Python depencies:
    
   .. code-block:: bash
   
      $ pip-3.2 install blinker filelock

#. Create the user that should run the EMSM:

   .. code-block:: bash
      
      $ addgroup --system --no-create-home --disabled-login --group minecraft
      $ adduser --system --no-create-home --disabled-login --ingroup minecraft minecraft
      
#. Create the EMSM root directory and switch to it:
   
   .. code-block:: bash
   
      $ mkdir /opt/minecraft
      $ cd /opt/minecraft

#. Download the latest stable EMSM version and extract it:

   .. code-block:: bash
      
      $ wget https://github.com/benediktschmitt/emsm/archive/master.tar.gz -O /tmp/emsm-master.tar.gz
      $ tar -xzf /tmp/emsm-master.tar.gz -C /tmp
      $ mv /tmp/emsm-master/* /opt/minecraft
      $ chown -R minecraft:minecraft /opt/minecraft
      
#. If you want, you can clean the EMSM folder up. You probably don't need the source
   of the documentation:
   
   .. code-block:: bash
   
      $ rm -r /opt/minecraft/docs
      $ rm -r /opt/minecraft/LICENSE
      $ rm -r /opt/minecraft/README.md

#. Make sure the the EMSM is executable:

   .. code-block:: bash
   
      $ chmod +x /opt/minecraft/minecraft.py
      
#. Add the EMSM application to your PATH:

   .. code-block:: bash

      $ ln -s /opt/minecraft/minecraft.py /usr/bin/minecraft
      
#. Intall the *init.d* service:

   .. code-block:: bash
   
      $ cp /opt/minecraft/emsm/initd_script /etc/init.d/minecraft
      $ chmod +x /etc/init.d/minecraft
      $ update-rc.d minecraft defaults

#. Well, that's all. For the first run, call a *passive* EMSM routine:

   .. code-block:: bash

      $ minecraft plugins --list
      
   This will create the some other directories and ``/opt/minecraft/`` should
   look similar to this:
   
   .. code-block:: none
   
      |- /opt/minecraft
         |- conf
         |- emsm
         |- logs
         |- minecraft.py
         |- plugins
         |- plugins_data
         |- server
         |- worlds
       
Known issues
------------

Running EMSM under another user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you run the application under another user than *minecraft*, you
have to edit the :file:`conf/main.conf` configuration file before you call the
EMSM the first time otherwise you will get an ``WrongUserError``:
   
.. code-block:: ini

   [emsm]
   user = foobar