:mod:`plugins`
==============

.. module:: plugins

Download
--------

You can find the latest version of this plugin in the EMSM 
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

About
-----

This is a package manager for EMSM plugins. Uninstall and install plugins with 
this plugin.

This plugin works only with valid packages and plugins that store its data in 
the dedicated paths.

Arguments
---------

.. option:: --install ARCHIVE, -i ARCHIV

   Installs an new plugin from the archive. If a plugin with the same name
   already exists, the installation will fail.    
   
.. option:: --remove PLUGIN, -r PLUGIN

   Removes the plugin from the EMSM. Please make sure, that no other plugin
   depends on this one.
   
.. option:: --doc PLUGIN, -d PLUGIN

   Prints the documentation of the selected plugin.

Package structure
-----------------

The archive that contains the plugin should have the following structure::

   \foo.tar.bz2
      \plugin.py
      \data
         \bar.txt
         \bar.csv
         \...

During the installation, the path names will be changed to::

   \
      \plugins_src
         \foo.py    <= plugin.py
      \plugins_data
         \foo       <= data
            \bar.txt
            \bar.csv
            \...

If the plugin contains a docstring like this one, it will be printed after
the installation.

Builder
-------

This plugin comes with an EMSM independent building script for new plugins.
This means, that you can call this script without having the EMSM environment.

Arguments
^^^^^^^^^

.. option:: --create TARGET, -c TARGET
.. option:: --source FILE, -s FILE
.. option:: --data DIRECTORY, -d DIRECTORY
.. option:: --help, -h

Example
^^^^^^^

Build the plugin *foo*, that comes with a data directory:

 .. code-block:: bash
   
   $ plugin.py -c build/foo -s dev/foo.py -d dev/foo_data
   $ ls build
   ... foo.tar.bz2 ...
