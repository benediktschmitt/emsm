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
:file:`__init__.py`. I guess it won't last longer than **1.5 hours** to read and
understand how the EMSM works.

About the depencies
-------------------

The EMSM depends on some tools and Python packages.

One of them (the most important) is
`screen <https://www.gnu.org/software/screen/manual/screen.html>`_, which is
used to run the minecraft worlds in the background.

We also depend on some Python packages, which are all available via PyPi.
