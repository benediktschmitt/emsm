.. _api:

API
===
   
.. toctree::
   :maxdepth: 1
   :titlesonly:
   :glob:
   
   * 

If you want to know, how the EMSM works, you are probably faster by reading 
the source code than this API documentation. The code is written to be read 
by other persons and quite easy to understand. Since the EMSM does not use
threads, you can simply follow the function calls, starting in 
:file:`EMSM_ROOT/minecraft.py`. I guess it won't last longer than **1.5 hours**
to read and understand how the EMSM works.

About the depencies
-------------------

The EMSM uses `screen <https://www.gnu.org/software/screen/manual/screen.html>`_
to run the minecraft server in the background.

It also depends on some Python packages, like `blinker <https://pythonhosted.org/blinker>`_
and `filelock <https://pypi.python.org/pypi/filelock/>`_, which are available 
via PyPi.