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

This plugins works as a tutorial. It's inspired by the wordpress plugin
`Hello Dolly <https://wordpress.org/plugins/hello-dolly/>`_.

Code and Download
-----------------

You can find the latest version of *hello_dolly* on the EMSM GitHub
`GitHub repository <https://github.com/benediktschmitt/emsm/blob/master/plugins/plugins.py>`_.

..
    By the way, this is a comment block in reST.

    The next line is a little hack. Unfortunetly, sphinx does not find
    "hellodolly.py" when this docstring is included with autodoc. So this does
    not work:

    .. literalinclude:: hellodolly.py

    The next line is actually a small hack. When the documentation is
    built, this module is included from
    ``EMSM_ROOT/docs/source/plugins/``, but the module is in
    ``EMSM_ROOT/plugins/```.

.. literalinclude:: ../../../emsm/plugins/hellodolly.py

Installation
------------

We want to distribute our plugin because we think it brings so much joy
to all players. So let's create a small package.

This is usually done with the :mod:`plugins.plugins` plugin:

.. code-block:: bash

    $ foo@bar: ls
    hellodolly.py ...
    $ foo@bar: plugin.py --source hellodolly.py
    $ foo@bar: ls
    hellodolly.py hellodolly.tar.bz2 ...

The compressed package archive should now be in your working directory.

Usage
-----

.. code-block:: bash

    $ foo@bar: # Will print only one row:
    $ foo@bar: minecraft -W hellodolly

    $ foo@bar: # Prints 5 rows or less, if the configuration value is smaller:
    $ foo@bar: minecraft -W hellodolly --rows 5

Documentation
-------------

Acutally, EMSM uses sphinx *autodoc* feature to create the documentation for
the plugins. So what, you see here is the docstring of the ``hellodolly.py``
module.
"""


# Modules
# ------------------------------------------------

# std
import os
import random

# third party
import termcolor

# local
import emsm
from emsm.core.base_plugin import BasePlugin


# Data
# ------------------------------------------------

# This variable helps the EMSM to find the actual plugin class in this module.
PLUGIN = "HelloDolly"

# These are the well-known hello dolly lyrics.
LYRICS = """Hello, Dolly
Well, hello, Dolly
It's so nice to have you back where you belong
You're lookin' swell, Dolly
I can tell, Dolly
You're still glowin', you're still crowin'
You're still goin' strong
We feel the room swayin'
While the band's playin'
One of your old favourite songs from way back when
So, take her wrap, fellas
Find her an empty lap, fellas
Dolly'll never go away again
Hello, Dolly
Well, hello, Dolly
It's so nice to have you back where you belong
You're lookin' swell, Dolly
I can tell, Dolly
You're still glowin', you're still crowin'
You're still goin' strong
We feel the room swayin'
While the band's playin'
One of your old favourite songs from way back when
Golly, gee, fellas
Find her a vacant knee, fellas
Dolly'll never go away
Dolly'll never go away
Dolly'll never go away again"""


# Classes
# ------------------------------------------------

class HelloDolly(BasePlugin):

    # We don't need to wait for other plugins, so we don't care
    # about the init priority. If you want that your plugin is initialised
    # earlier than others, make this value smaller.
    INIT_PRIORITY = 0

    # Also, we don't care about if the finish method of our plugin is called
    # early or late. The *finish* method of plugins with a smaller
    # *FINISH_PRIORITY* is called earlier.
    FINISH_PRIORITY = 0

    # At the moment, there is no direct url to the latest version of this
    # plugin.
    # In the future, the plugin manager could use this url to detect new
    # versions of your plugin and will download them automatically.
    DOWNLOAD_URL = None

    # The last compatible version of the EMSM.
    VERSION = "5.0.0-beta"

    # The EMSM automatically uses the DESCRIPTION variable to set up the
    # *--long-help* argument parser argument.
    #
    # We ususally use here the module's docstring. Note, that ``__doc__``
    # does not interfere with the HelloDolly docstring ``HelloDolly.__doc__``
    # since the HelloDolly class has no docstring.
    DESCRIPTION = __doc__

    def __init__(self, application, name):
        """
        """
        # We need to init the BasePlugin. This is necessairy, so that we can
        # safely access:
        #
        #   * self.global_conf()
        #   * self.argparser()
        #   * ...
        BasePlugin.__init__(self, application, name)

        # The configuration and argument parser are set up in own methods
        # for readability.
        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        Sets the global configuration up. (The ``hellodolly`` section in
        :file:`main.conf`)
        """
        # Get the configuration dictionary for this plugin.
        conf = self.global_conf()

        # This is an example of the hellodolly configuration section in the
        # main.conf configuration file:
        #
        # [hellodolly]
        # max_rows = 5
        #

        self._max_rows = conf.getint("max_rows", 5)
        conf["max_rows"] = str(self._max_rows)
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        # Get the plugin's argument parser.
        parser = self.argparser()

        parser.description = (
            "Demonstrates the implementation of a plugin. Inspired by the "
            "wordpress plugin \"Hello, Dolly\"."
            )
        parser.epilog = "https://github.com/benediktschmitt/emsm"

        # Note, that we prefix the *dest* value, since all arguments share
        # the same namespace.
        parser.add_argument(
            "--rows", "-r",
            action = "store",
            dest = "hellodolly_rows",
            type = int,
            default = 1,
            metavar = "ROWS",
            help = "The number of lines that will be printed."
            )
        return None

    def _uninstall(self):
        """
        If you created data not stored in ``data_dir()`` or used also the
        *worlds.conf* or *server.conf* configuration files, you should ask the
        user here, if he wants to remove these files and settings too.

        Note the difference between ``_uninstall()`` and ``uninstall()``.
        """
        # Your uninstallation stuff here
        # ...
        return None

    def run(self, args):
        """
        Writes lines of our lyrics into the chats of the selected worlds.

        Parameters:
            * args
                Is a namespace that contains the parsed arguements.
        """
        # Get the number of lines we want to print and make sure, that
        # the number is not greater then the max_rows configuration value.
        rows = args.hellodolly_rows
        if rows > self._max_rows:
            rows = self._max_rows
        if rows < 0:
            rows = 0

        # Run hellodolly for each world, which has been selected with
        # *-w* or *-W* per command line.
        # We sort the worlds by their names, to process them in alphabetical
        # order.
        worlds = self.app().worlds().get_selected()
        worlds.sort(key = lambda w: w.name())

        for world in worlds:
            self.be_poetic(world, rows)
        return None

    def get_lyrics(self, num_rows):
        """
        Returns rows of the hello dolly lyrics.

        Parameters:
            * num_rows
                The number of rows, that should be extracted from the
                lyrics.
        """
        global LYRICS
        lyrics = LYRICS

        # Get *num_rows* lines of the lyrics.
        lyrics = lyrics.split("\n")
        if num_rows > len(lyrics):
            return lyrics
        else:
            a = random.randint(0, len(lyrics) - num_rows)
            lyrics = lyrics[a:a+num_rows]
        return lyrics

    def be_poetic(self, world, num_rows):
        """
        Writes the *lyrics* to the chat of all running, selected worlds.
        """
        lyrics = self.get_lyrics(num_rows)

        # We follow the inofficial EMSM style guide and print the
        # world name in cyan.
        print(termcolor.colored("{}:".format(world.name()), "cyan"))
        if world.is_offline():
            print("\t", termcolor.colored("error:", "red"), "world is offline")
        else:
            for row in lyrics:
                world.send_command("say {}".format(row))
            print("\t", "world has been visited")
        return None

    def finish(self):
        """
        This method is always called, when the EMSM is about to finish.
        It should be used for clean up or background stuff.
        """
        return None
