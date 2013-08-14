#!/usr/bin/env python3


# Modules
# ------------------------------------------------
import os
import random

# local
from base_plugin import BasePlugin


# Vars
# ------------------------------------------------
# This string variable contains the name of the plugin
# class in this module.
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
    This plugin is inspired by the wordpress plugin
    *Hello Dolly*.
    """

    version = "1.0."

    def __init__(self, application, name):
        # We need to init the BasePlugin. It will create
        # the references we'll use.
        BasePlugin.__init__(self, application, name)

        # Configuration

        # This is the number of rows that we want to allow to
        # print at once.
        self.max_rows = self.conf.getint("max_rows", 5)
        self.conf["max_rows"] = str(self.max_rows)
        
        # Here, we store the used lyrics.
        self.lyrics_file = os.path.join(self.data_dir, "lyrics.txt")

        # If the lyrics file does not exist, we'll init
        # it with the default lyrics.
        if not os.path.exists(self.lyrics_file):
            with open(self.lyrics_file, "w") as file:
                file.write(_DEFAULT_LYRICS)
        return None

    # run
    # --------------------------------------------
    
    def setup_argparser_argument_group(self, group):
        """
        Add the hello dolly arguments to the argparser.
        """
        group.title = self.name
        group.description = "Demonstrates the implementation of a "\
                            "plugin. Inspired by the wordpress plugin "\
                            "\"Hello, Dolly\"."

        # Add our arguments.
        group.add_argument(
            "--rows", "-r",
            action="store", dest="hello_dolly_rows", type=int,
            default=1, metavar="ROWS",
            help="The number of lines that will be printed. ")
        return None

    def run(self, args):
        """
        Writes lines of our lyrics into the chats
        of the selected worlds.
        """
        if args.hello_dolly_rows < self.max_rows:
            rows = args.hello_dolly_rows
        else:
            rows = self.max_rows

        lyrics = self.get_lyrics(rows)
        self.be_poetic(lyrics)
        return None

    def get_lyrics(self, rows):
        """
        Returns rows of the hello dolly lyrics.
        """
        with open(self.lyrics_file) as file:
            lyrics = list(file)

        if rows > len(lyrics):
            return lyrics
        else:
            a = random.randint(0, len(lyrics) - rows)
            lyrics = lyrics[a:a+rows]
        return lyrics


    def be_poetic(self, lyrics):
        """
        Writes the lyrics to the chat of all running, selected worlds.
        """
        worlds = self.application.world_manager.get_selected_worlds()
        
        for world in worlds:
            if not world.is_online():
                continue
            print("Poet visits '{}'.".format(world.name))
            for row in lyrics:
                world.send_command("say {}".format(row))
        return None

    # end
    # --------------------------------------------

    def finish(self):
        """
        Print a row of the lyrics to the command line to greet
        the user.

        This method is always called.
        """
        # I think this is quite annoying so I commented this
        # section out.
        
##        rows = self.get_lyrics(1)
##        row = rows[0].strip()
##        print("hello_dolly greets you:", row)
        return None
