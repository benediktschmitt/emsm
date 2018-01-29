First steps
===========

There are some common arguments and run types you should know:

*   The **help** argument:

    .. code-block:: bash

        $ minecraft -h
        $ minecraft worlds -h
        $ minecraft server -h
        $ minecraft backups -h
        ...

*   The **long-help** argument:

    .. code-block:: bash

        $ minecraft worlds --long-help
        $ minecraft backups --long-help
        ...

Each plugin provides its own arguments, similar to *git*. There are only a few
**global arguments** to unify the interface:

*   Select all worlds:

    .. code-block:: bash

        $ minecraft -W [plugin ...]
        $ minecraft --all-worlds [plugin ...]

*   Select world by world:

    .. code-block:: bash

        $ minecraft -w foo -w bar [plugin ...]
        $ minecraft --world foo --world bar [plugin ...]

*   Select all server software:

    .. code-block:: bash

        $ minecraft -S [plugin ...]
        $ minecraft --all-server [plugin ...]

*   Select server by server:

    .. code-block:: bash

        $ minecraft -s vanilla -s bukkit [plugin ...]
        $ minecraft --server vanilla --server bukkit [plugin ...]

Common tasks
------------

*   Start all worlds:

    .. code-block:: bash

        $ minecraft -W worlds --start
        $ minecraft --all-worlds worlds --start

    .. note::

        Please note, that the *first start* of a world may fail, if the *eula*
        has not been accepted.

*   Restart one world:

    .. code-block:: bash

        $ minecraft -w foo worlds --restart
        $ minecraft --world foo worlds --restart
        $ minecraft -w foo worlds --force-restart

*   Stop all worlds:

    .. code-block:: bash

        $ minecraft -W worlds --stop
        $ minecraft --all-worlds worlds --stop

*   Server update:

    .. code-block:: bash

        $ minecraft -S server --update
        $ minecraft -s "vanilla 1.8" server --update
        $ minecraft --server "vanilla 1.8" server --update

    Make sure to read the next section for more information about server updates.
