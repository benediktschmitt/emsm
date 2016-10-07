#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2014-2016 Benedikt Schmitt <benedikt@benediktschmitt.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
About
-----

Works as interface between the linux *initd service* and the EMSM.

Download
--------

You can find the latest version of this plugin in the EMSM
`GitHub repository <https://github.com/benediktschmitt/emsm>`_.

Installation
------------

You can use this plugin with *initd* or *systemd*.

initd (:file:`/etc/init.d/`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You only have to create the ``init.d`` script :file:`/etc/init.d/minecraft`:

..  literalinclude:: ../../../emsm/core/initd_script.sh
    :language: bash
    :linenos:

.. code-block:: bash

    $ sudo chmod +x /etc/init.d/minecraft
    $ sudo update-rc.d minecraft defaults
    $ sudo update-rc.d minecraft enable

systemd (:file:`/etc/systemd/system/minecraft.service`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You only have to create the :file:`/etc/systemd/system/minecraft.service` file:

..  literalinclude:: ../../../emsm/core/systemd.service
    :language: bash
    :linenos:

.. code-block:: bash

    $ sudo systemctl daemon-reload
    $ sudo systemctl enable minecraft.service

Configuration
-------------

\*.worlds.conf
^^^^^^^^^^^^^^

.. code-block:: ini

    [plugin:initd]
    enable = yes

**enable**

    If ``yes``, the autostart/-stop is enabled.

Arguments
---------

.. option:: --start

    Starts all worlds, where initd has been enabled in the
    :file:`*.world.conf` configuration file.

.. option:: --stop

    Stops all worlds, where initd is enabled.
    Note, that this will always **force** the stop of the world, since the
    process is killed anyway during system shutdown.

.. option:: --restart

    Forces the restart of all worlds, for which initd has been enabled.

.. option:: --status

    Prints the status (online/offline) for each *initd* enabled world.

Exit code
---------

The exit code is set to:

* 0 if no error occured.
* 2 if an error occured.

Changelog
---------

EMSM v5
^^^^^^^

*   *initd* must now be enabled in the *plugin:initd* configuration
    section of the :file:`*.world.conf` configuration file.

    In v4 (:file:`worlds.conf`):

    .. code-block:: ini

        [morpheus]
        enable_initd = yes

    In v5 (:file:`morpheus.world.conf`):

    .. code-block:: ini

        [plugin:initd]
        enable = yes
"""


# Modules
# ------------------------------------------------

# std
import logging

# third party
import blinker
import termcolor

# local
import emsm
from emsm.core.base_plugin import BasePlugin


# Data
# ------------------------------------------------

PLUGIN = "InitD"

log = logging.getLogger(__file__)


# Classes
# ------------------------------------------------

class InitD(BasePlugin):

    VERSION = "5.0.0-beta"

    DESCRIPTION = __doc__

    # Emitted when initd is called with the *--start* argument.
    on_initd_start = blinker.signal("initd_start")

    # Emitted when initd is called with the *--stop* argument.
    on_initd_stop = blinker.signal("initd_stop")

    # Emitted when initd is called with the *--restart* argument.
    on_initd_restart = blinker.signal("initd_restart")

    def __init__(self, app, name):
        """
        """
        BasePlugin.__init__(self, app, name)

        self._setup_argparser()
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        parser = self.argparser()

        parser.description = "InitD interface"

        # Allow only one runlevel to the same time.
        me_group = parser.add_mutually_exclusive_group()
        me_group.add_argument(
            "--start",
            action = "count",
            dest = "initd_start",
            help = "Starts all worlds for which initd support is enabled."
            )
        me_group.add_argument(
            "--stop",
            action = "count",
            dest = "initd_stop",
            help = "Stop all worlds for which initd support is enabled."
            )
        me_group.add_argument(
            "--restart",
            action = "count",
            dest = "initd_restart",
            help = "Restart all worlds for which initd support is enabled."
            )
        me_group.add_argument(
            "--status",
            action = "count",
            dest = "initd_status",
            help = "Prints the status of all initd managed worlds."
            )
        return None

    def _initd_worlds(self):
        """
        Returns all worlds where *conf[plugin:initd][enable]* is true.
        The worlds are sorted by their names.

        See also:
            * WorldWrapper.conf()
        """
        worlds = list()
        for world in self.app().worlds().get_all():
            # Initialise the configuration on the fly.
            world_conf = self.world_conf(world)
            enable = world_conf.getboolean("enable", False)
            world_conf["enable"] = "yes" if enable else "no"

            if world_conf.getboolean("enable"):
                worlds.append(world)

        worlds.sort(key = lambda w: w.name())
        return worlds

    def _start(self):
        """
        Starts all worlds if *initd* is enabled.
        """
        # We create the unformatted messages here to increase readability.
        raw_msg = "[ {status} ] starting the minecraft world '{{world_name}}'"
        pre_msg = raw_msg.format(status="... ")
        fail_msg = raw_msg.format(status=termcolor.colored("fail", "red"))
        ok_msg = raw_msg.format(status=termcolor.colored("ok  ", "green"))

        # Start the worlds.
        log.info("initd start ...")

        for world in self._initd_worlds():
            print(pre_msg.format(world_name=world.name()), end="\r")
            try:
                world.start()
            except emsm.core.worlds.WorldStartFailed as err:
                print(fail_msg.format(world_name=world.name()))
                self.app().set_exit_code(2)
            else:
                print(ok_msg.format(world_name=world.name()))

        log.info("initd start done.")
        return None

    def _stop(self):
        """
        Stops all worlds if *initd* is enabled.
        """
        # We create the unformatted messages here to increase readability.
        raw_msg = "[ {status} ] stopping the minecraft world '{{world_name}}'"
        pre_msg = raw_msg.format(status="... ")
        fail_msg = raw_msg.format(status=termcolor.colored("fail", "red"))
        ok_msg = raw_msg.format(status=termcolor.colored("ok  ", "green"))

        # Stop the worlds.
        log.info("initd stop ...")

        for world in self._initd_worlds():
            print(pre_msg.format(world_name=world.name()), end="\r")
            try:
                # Because the process is killed anyway, we force it here.
                world.stop(force_stop=True)
            except emsm.core.worlds.WorldStopFailed as err:
                print(fail_msg.format(world_name=world.name()))
                self.app().set_exit_code(2)
            else:
                print(ok_msg.format(world_name=world.name()))

        log.info("initd stop done.")
        return None

    def _restart(self):
        """
        Forces the restart of all worlds which have initd enabled.
        """
        # We create the unformatted messages here to increase readability.
        raw_msg = "[ {status} ] restarting the minecraft world '{{world_name}}'"
        pre_msg = raw_msg.format(status="... ")
        fail_msg = raw_msg.format(status=termcolor.colored("fail", "red"))
        ok_msg = raw_msg.format(status=termcolor.colored("ok  ", "green"))

        # Restart the worlds.
        log.info("initd restart ...")

        for world in self._initd_worlds():
            print(pre_msg.format(world_name=world.name()), end="\r")
            try:
                # Because the process is killed anyway, we force it here.
                world.restart(force_restart=True)
            except emsm.core.worlds.WorldStopFailed as err:
                print(fail_msg.format(world_name=world.name()))
                self.app().set_exit_code(2)
            except emsm.core.worlds.WorldStartFailed as err:
                print(fail_msg.format(world_name=world.name()))
                self.app().set_exit_code(2)
            else:
                print(ok_msg.format(world_name=world.name()))

        log.info("initd restart done.")
        return None

    def _status(self):
        """
        Prints the status of all worlds where initd has been enabled.
        """
        # We create the unformatted messages here to increase readability.
        fail_msg = "[ {status} ] the minecraft world '{{world_name}}' is offline."\
                   .format(status=termcolor.colored("fail", "red"))
        ok_msg = "[ {status} ] the minecraft world '{{world_name}}' is online."\
                 .format(status=termcolor.colored("ok  ", "green"))

        # Print the status the worlds.
        for world in self._initd_worlds():
            if world.is_online():
                print(ok_msg.format(world_name=world.name()))
            else:
                print(fail_msg.format(world_name=world.name()))
        return None

    def run(self, args):
        """
        """
        if args.initd_start:
            self._start()
            InitD.on_initd_start.send()
        elif args.initd_stop:
            self._stop()
            InitD.on_initd_stop.send()
        elif args.initd_restart:
            self._restart()
            InitD.on_initd_restart.send()
        elif args.initd_status:
            self._status()
        return None
