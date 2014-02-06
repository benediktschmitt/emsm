:mod:`status`
=============

.. module:: status

About 
-----

This plugin is passive and does not send any command to a server. Furthermore,
it never changes the status of a world. It only creates a **status report** for 
each world and distributes it via email or json.

This plugin creates always a complete status report. This means, that the status
of *all* worlds is included.

Download
--------

You can find the latest version of this plugin in the **EMSM**  
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.
   
Configuration
-------------

.. code-block:: ini

   [status]
   email_to = root
   email_from = minecraft
   email_stmp_starttls = yes
   email_smtp_host = localhost
   email_smtp_port = 25
   email_smtp_user = 
   email_smtp_pass = 
   json_autorun = no
   json_path = 

**email_to**

   Is the recipient of the mail.

**email_from**

   Is the sender of the mail

**email_smtp_starttls**

   Will result in the use of STARTTLS if 'yes'.

**email_stmp_host**

   Is the hostname of the stmp server.

**email_smtp_port**

   Is the port of the smtp server

**email_smtp_user**

   Is the username that is used to auth the client at the smtp server.

**email_stmp_pass**

   .. attention:: 
   
      When you have to set this option, make sure, that you use **STARTLS**
      and that the configuration file is not readable for other persons.

   Is the password used to auth the client at the smtp server.

**json_autorun**

   If yes, the json status file will be updated each time, the EMSM runs.

**json_path**

   Alternative path for the json status file. The default path is the
   plugins data folder.
   
Arguments
---------

.. option:: --json
   
   Creates the json status report
   
.. option:: --mail

   Creates the status report and sends it per mail
   
Cron
----

This plugin is very useful, when you use it with cron. This crontab will send
you a status report at 2:00h:

.. code-block:: text
   
   # m h dom mon dow user command
   5   2 *   *   *   root minecraft -W guard