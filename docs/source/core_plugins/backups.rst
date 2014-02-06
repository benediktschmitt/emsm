:mod:`backups`
==============

.. module:: backups

About
-----

Extends the EMSM by a backup manager.

Download
--------

You can find the latest version of this plugin in the EMSM
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.
   
Configuration
-------------

.. code-block:: ini

   [backups]
   archive_format = bztar
   restore_message = This world is about to be ressetted to an earlier state.
   restore_delay = 5
   max_storage_size = 30
   auto_sync = yes
   mirrors =
   
**archive_format**

   Is the name of the archive format used to create the backups. This string has
   to be listed in *shutil.get_archive_formats()*. Usually, there should be at
   least *zip* or *tar* available.
   
**restore_message**

   Is send to the world's chat before restoring the world.
    
**restore_delay**

   Seconds between sending the *restore_message* to the chat and starting
   the restore.
   
**max_storage_size**

   Maximum number of backups in the storage folder, before older backups
   will be removed.
   
**auto_sync**

   If yes, the backup mirrors will be sync each time the EMSM runs.
   
**mirrors**

   Comma (,) separated list of the backup directories.
   
Arguments
---------

.. note::

   All arguments will only affect the worlds selected with *--world* or
   *--all-world*
   
.. option:: --list

   Lists all available backups.
   
.. option:: --sync

   Synchronises and cleans all backup mirrors.

.. option:: --create

   Creates a new backup.
 
.. option:: --restore PATH

   Restores the world with the backup from the given BACKUP_PATH.
 
.. option:: --restore-latest

   Restores, if available, the latest backup of the world.
 
.. option:: --restore-menu

   Opens a menu, where the user can select which backup he wants to restore.