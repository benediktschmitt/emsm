:mod:`hellodolly`
==================

.. module:: hellodolly

About
-----

This plugins works as a tutorial. It's inspired by the wordpress plugin
`Hello Dolly <https://wordpress.org/plugins/hello-dolly/>`_. 

Download
--------

You can find the latest version on
`GitHub <https://github.com/benediktschmitt/emsm/>`_.

Or you download the version used to create this documentation file
:download:`here <hellodolly.py>`.

Code
----

.. literalinclude:: hellodolly.py

Package
-------

Now, we want to create our own plugin package, so that the user can install it
with :mod:`plugins`:

.. code-block:: bash

   $ plugin.py -s hellodolly.py
   $ ls
   hellodolly.py hellodolly.tar.bz2 ...
   
The package should be now in your current working directory.
   
Usage
-----

.. code-block:: bash

   # Will print only one row:
   minecraft -W hellodolly
   
   # Prints 5 rows or less, if the configuration value is smaller:
   minecraft -W hellodolly --rows 5
   
Documentation
------------- 

To view the source code of this documentation file, click on the **Source**
link in the navigation bar. 
   