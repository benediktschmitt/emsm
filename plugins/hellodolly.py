#!/usr/bin/python3

# The MIT License (MIT)
# 
# Copyright (c) 2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
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
=====
The main purpose of this plugin is to demonstrate the implementation of an
EMSM plugin.


Configuration
=============
[hellodolly]
max_rows = 5

Where
-----
* max_rows
    Is the maximum number of lines printed at once.


Arguments
=========
* --rows ROWS, -r ROWS
    Number of rows to print.


Note
====
Note, that this docstring should be helpful, despite to the fact, that the
user can access this easily for further information with this plugin.

    $ minecraft plugins --doc hellodolly
"""


# Modules
# ------------------------------------------------
import os
import random

# local
from base_plugin import BasePlugin


# Vars
# ------------------------------------------------
# This string variable contains the name of the plugin class in this module.
PLUGIN = "HelloDolly"


# These are the well-known hello dolly lyrics.
_DEFAULT_LYRICS = """Hello, Dolly
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
Dolly'll never go away again
"""


# Classes
# ------------------------------------------------
class HelloDolly(BasePlugin):
    """
    This plugin is inspired by the wordpress plugin *Hello Dolly*. Its primary
    purpose is to demonstrate the implementation of a plugin.

    It demonstrates the use of:
        * self.app
        * self.name
        * self.log
        * self.conf
        * self.data_dir
        * self.argparser
    """

    # We don't need to wait for other plugins, so we don't care
    # about the init priority. If you want that your plugin is initialised
    # earlier than others, make this value smaller.
    #init_priority = 0

    # Also, we don't care about the fact if the finish method of our
    # plugin is called early or late. The *finish* method of plugins with
    # a smaller *finish_priority* is called earlier.
    #finish_priority = 0

    # At the moment, there is no direct url to the latest version of this
    # plugin. The plugin manager can use this url to detect new versions of
    # your plugin and will download them (almost) automatically.
    #download_url = ""
    
    # The last compatible version of the EMSM
    version = "2.0.0"

    def __init__(self, application, name):
        # We need to init the BasePlugin. It will create the references
        # described above.
        BasePlugin.__init__(self, application, name)

        # Configuration

        # This is the number of rows that we want to allow to print at once.
        self.max_rows = self.conf.getint("max_rows", 5)
        self.conf["max_rows"] = str(self.max_rows)
        
        # Here, we store the used lyrics.
        self.lyrics_file = os.path.join(self.data_dir, "lyrics.txt")

        # If the lyrics file does not exist, we'll init it with the default
        # lyrics.
        if not os.path.exists(self.lyrics_file):
            with open(self.lyrics_file, "w") as file:
                file.write(_DEFAULT_LYRICS)

        # Now, we set our argparser up.
        self.argparser.description = (
            "Demonstrates the implementation of a plugin. Inspired by the "
            "wordpress plugin \"Hello, Dolly\"."
            )
        self.argparser.epilog = "https://emsm.benediktschmitt.de/"
        self.argparser.add_argument(
            "--rows", "-r",
            action="store", dest="rows", type=int,
            default=1, metavar="ROWS",
            help="The number of lines that will be printed. "
            )
        return None

    def uninstall(self):
        """
        If you created data not stored in *self.data_dir* or used also the
        *worlds.conf* or *server.conf* configuration files, you should ask the
        user here, if he wants to remove these files and settings too.
        """
        # Don't forget to call the BasePlugins uninstall method. This will
        # remove (if wished) the data directory of the plugin and the
        # configuration.
        super().uninstall()

        # Your stuff here. E.g.:
        #for section in self.app.conf.worlds:
        #    self.app.conf.worlds.remove_option(section, "my_awesome_conf")
        return None

    # run
    # --------------------------------------------

    def run(self, args):
        """
        Writes lines of our lyrics into the chats of the selected worlds.
        """
        rows = args.rows if args.rows < self.max_rows else self.max_rows
        lyrics = self.get_lyrics(rows)
        self.be_poetic(lyrics)
        return None

    def get_lyrics(self, num_rows):
        """
        Returns rows of the hello dolly lyrics.
        """
        with open(self.lyrics_file) as file:
            lyrics = list(file)

        if num_rows > len(lyrics):
            return lyrics
        else:
            a = random.randint(0, len(lyrics) - num_rows)
            lyrics = lyrics[a:a+num_rows]
        return lyrics

    def be_poetic(self, lyrics):
        """
        Writes the lyrics to the chat of all running, selected worlds.
        """
        worlds = self.app.worlds.get_selected()
        for world in worlds:
            if not world.is_online():
                continue

            # We can also log what we are doing. 
            msg = "Poest visits '{}'".format(world.name)
            self.log.debug(msg)
            print(msg)
            
            for row in lyrics:
                world.send_command("say {}".format(row))
        return None

    # end
    # --------------------------------------------

    def finish(self):
        """
        Print a row of the lyrics to the command line to greet the user.

        This method is always called.
        """
        # I think this is quite annoying so I commented this
        # section out.
        
##        rows = self.get_lyrics(1)
##        row = rows[0].strip()
##        print("hello_dolly greets you:", row)
        return None
