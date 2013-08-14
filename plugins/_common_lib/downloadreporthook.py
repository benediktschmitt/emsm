#!/usr/bin/env python


# Modules
# ------------------------------------------------
import time


# Classes
# ------------------------------------------------
class Reporthook(object):
    """
    Prints a progress bar and other download related information
    every hook.
    """

    def __init__(self, screen_width=75, print_intervall=0.5,
                 url=str(), to_file=str()):
        # Constant values
        self.print_intervall = float(print_intervall)
        self.screen_width = int(screen_width)
        self.url = str(url)
        self.to_file = str(to_file)

        # Values, that will be initialised at start.
        self._start_time = 0

        # Progress at last output
        # (needed to calc new information)
        self._state_last_hook = dict()
        self._state_last_hook["time"] = 0
        self._state_last_hook["progress"] = 0
        self._state_last_hook["downloaded"] = 0
        return None

    # help methods
    # --------------------------------------------
    
    def get_bar(self, progress):
        """
        Returns the progress-bar string.
        E.g.:
        [======>      ]
        """
        bar_length = self.screen_width - 25
        if bar_length >= 10:
            bar_arrow_length = round(bar_length * progress)
            bar = " [" +\
                  "-"*(bar_arrow_length) + ">" +\
                  " "*(bar_length - bar_arrow_length) +\
                  "] "
        else:
            bar = str()
        return bar

    def filesize_to_string(self, size):
        """
        >>> filesize_to_string(49811456)
        4.77mb
        """
        units = ["b", "kb", "mb", "gb", "tb", "eb"]

        i = 0
        while i < len(units)-1 and size >= 1024:
            size /= 1204
            i += 1
        
        temp = "{:,.0f}{}".format(size, units[i])
        return temp
    
    # download
    # --------------------------------------------
    
    def _download_starts(self, blocks, blocksize, size):
        # Start time
        self.start_time = time.time()        

        self._state_last_hook["time"] = time.time()
        self._state_last_hook["progress"] = 0
        self._state_last_hook["downloaded"] = 0        

        if self.url:
            print("Download of '{}' started.".format(self.url))
        else:
            print("Download started.")            
            
        if self.to_file:
            print("    -> saving in '{}".format(self.to_file))
        return None

    def _download_finished(self, blocks, blocksize, size):
        elapsed_time = time.time() - self.start_time
        elapsed_time = time.strftime("%Hh %Mmin %Ss", time.gmtime(elapsed_time))        

        size = self.filesize_to_string(size)
        
        temp = "Download complete. ({} in {})".format(size, elapsed_time)
        print()
        print(temp)
        return None    

    def _download_in_progress(self, blocks, blocksize, size):
        progress = blocks * blocksize / size
        if progress > 1 or progress < self._state_last_hook["progress"]:
            progress = 1
            
        downloaded = size * progress                
        self._state_last_hook["time"] = time.time()
        self._state_last_hook["progress"] = progress
        self._state_last_hook["downloaded"] = downloaded
        
        bar = self.get_bar(progress)
        downloaded = self.filesize_to_string(downloaded)
        total_size = self.filesize_to_string(size)

        temp = "{:>7.2%} {:1} {} / {}"\
               .format(progress, bar, downloaded, total_size)
        temp = temp.ljust(self.screen_width)
        temp = temp[:self.screen_width]
        print(temp, end="\r")
        return None
    
    def __call__(self, blocks, blocksize, size):
        """
        Prints the progress of the download.
        """
        if size == -1:
            return None

        # Progress   
        progress = blocks * blocksize / size
        if progress > 1 or progress < self._state_last_hook["progress"]:
            progress = 1
        
        # Download starts
        #   -> init statistic
        if progress == 0:
            self._download_starts(blocks, blocksize, size)

        # If download starts, ends or the print intervall forces an output:
        if progress == 0 or progress == 1 \
           or time.time() > self._state_last_hook["time"] + self.print_intervall:
            self._download_in_progress(blocks, blocksize, size)

        # Download is complete
        if progress == 1:
            self._download_finished(blocks, blocksize, size)
        return None
