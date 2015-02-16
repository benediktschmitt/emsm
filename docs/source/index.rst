Welcome to Extendable Minecraft Server Manager's documentation!
===============================================================

.. toctree::
    :maxdepth: 1

    how_to/index
    plugins/index
    api/index
    changelog
    contribute
    license
    about

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

What is the **EMSM** ?
----------------------

The **Extendable Minecraft Server Manager** (EMSM) is a minecraft server
wrapper, that is able to handle multiple minecraft worlds and server versions.

The **EMSM** itself provides only a simple but sufficient **API** to manage the
worlds. The rest of the work is done by the plugins. This makes the application
easy to extend and maintain.

Why should you use the **EMSM**?
--------------------------------

*   **Python powered**

    Small and readable code base, therefore easy to maintain.

*   **Open Source**

    Licensed under the :ref:`MIT License <license>`.

*   **Portable**

    Needs only Python, screen and java to run and should work on all Linux systems.

*   **Cron-Save**

    The EMSM makes sure, that only one instance of the application runs
    to the same time.

*   **InitD**

    Use the :mod:`emsm.plugins.initd` plugin to benefit from the *init.d* service.

*   **Simple Configuration**

    Only three simple configuration files with the simple *.ini* syntax.

*   **Backup ready**

    Create and manage multiple versions of your worlds with the
    :mod:`backup manager <emsm.plugins.backups>`.

*   **Multiple worlds and server**

    This application has been written to administrate and run multiple
    worlds and server versions to the same time.

*   **Beautiful output**

    The EMSM output is colored, so that you only need one view to get the
    most important information.

*   **Guarded worlds**

    The :mod:`plugins.guard` helps you to monitor the worlds and to react
    on server issues automatically.

*   **Fast learning curve**

    Use the ``--help`` or ``--long-help`` argument if you don't know how
    to use a plugin.

*   **Online Documentation**

    You don't come to grips with the configuration? Take a look at this
    online documentation.

*   **Easy to extend**

    Extend the EMSM with a simple plugin and benefit from Pythons great
    standard library.

Collaboration
-------------

.. figure:: /_static/logo/octocat_small.png
    :align: center

    ..

    **Fork** this project on `GitHub <https://github.com/benediktschmitt/emsm/>`_.
