#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


import time
import subprocess
import urllib.request


__all__ = ["Reporthook"]


def filesize_to_string(size):
    """
    Downsizes a file size.
    >>> filesize_to_string(49811456)
    '4.77mb'
    """
    units = ["b", "kb", "mb", "gb", "tb", "eb"]

    i = 0
    while i < len(units) - 1 and size >= 1024:
        size /= 1204
        i += 1
    
    temp = "{:,.0f}{}".format(size, units[i])
    return temp


def terminal_width(default=80):
    """
    Returns the current terminal width.
    Uses *default* as fallback.
    """
    def bash_width():        
        try:
            width = subprocess.check_output(["tput", "cols"])
            return int(width)
        except:
            return None
        
    def windows_width():
        return None
    
    width = bash_width()
    if width is None:
        width = windows_width()
    if width is None:
        width = default
    return width
    

class Reporthook(object):
    """
    Nice reporthook for the *urllib.request.urlretrieve* function.
    
    >>> myhook = Reporthook(
            url="http://www.eso.org/public/archives/images/publicationtiff10k/eso1242a.tif",
            target="milky_way.tif"
            )
    >>> urllib.request.urlretrieve(myhook.url, myhook.target, myhook)
    """

    def __init__(self, url, target=None, terminal_width=terminal_width,
                 update_intervall=1):
        if terminal_width is None:
            terminal_width = lambda: 80
        elif not callable(terminal_width):
            terminal_width = lambda: terminal_width
            
        # Constant values
        self.url = url
        self.target = target
        self.update_intervall = update_intervall
        self.terminal_width = terminal_width

        # We need some values to calculate additional information about
        # the progess.
        self._start_time = 0

        self._last_hook = {
            "time": 0,
            "progress": 0,
            "downloaded": 0
            }
        return None

    def get_bar(self, progress, bar_width=10):
        """
        Returns the progress-bar string.
        Example:
        [======>      ]
        """
        if bar_width < 10:
            return str()

        max_arrow_length = bar_width - 3
        arrow_length = max_arrow_length * progress
        arrow_length = max(0, round(arrow_length))
        bar = "[" +\
              "-"*arrow_length + ">" + " "*(max_arrow_length - arrow_length) +\
              "]"
        return bar
    
    def _download_starts(self, blocks, blocksize, size):
        """
        Called, when the download begins.
        """
        self.start_time = time.time()

        self._last_hook["time"] = time.time()
        self._last_hook["progress"] = 0
        self._last_hook["downloaded"] = 0

        print("Download started ...")
        print("-> time:", time.ctime())
        if self.url:
            print("-> url:", self.url)
        if self.target:
            print("-> target:", self.target)
        return None

    def _download_finished(self, blocks, blocksize, size):
        """
        Called, when the download is complete.
        """
        elapsed_time = time.time() - self.start_time
        elapsed_time = time.strftime("%Hh %Mmin %Ss", time.gmtime(elapsed_time))
        
        size = filesize_to_string(size)
        
        msg = "Download complete. ({} in {})".format(size, elapsed_time)
        print("\n", msg, sep="")
        return None

    def _download_in_progress(self, blocks, blocksize, size):
        """
        Called, if the download is in progress.
        """
        progress = blocks*blocksize / size
        # XXX I don't know if this is a bug in urllib.
        if progress > 1 or progress < self._last_hook["progress"]:
            progress = 1
            
        downloaded = size*progress  
        self._last_hook["time"] = time.time()
        self._last_hook["progress"] = progress
        self._last_hook["downloaded"] = downloaded

        # width:
        #   percentage: 7
        #   arrow: dynamic
        #   downloaded / size: width <= 15
        #   spaces between percentage and downloaded: 2
        #   \r: 1

        terminal_width = self.terminal_width() - 1
        
        progress_str = "{:>7.2%}".format(progress)        
        download_str = "{} / {}".format(
            filesize_to_string(downloaded),
            filesize_to_string(size)
            )
        download_str = download_str.rjust(15)
        bar_str = self.get_bar(
            progress,
            terminal_width - len(progress_str) - len(download_str) - 2
            )
        
        msg = progress_str + " " + bar_str + " " + download_str
        msg = msg.ljust(terminal_width)
        msg = msg[:terminal_width]
        print(msg, end="\r")
        return None

    def __call__(self, blocks, blocksize, size):
        """
        Prints the progress of the download.
        """
        if size == -1:
            return None

        progress = blocks*blocksize / size
        if progress > 1 or progress < self._last_hook["progress"]:
            progress = 1

        # Download begins ...
        if progress == 0:
            self._download_starts(blocks, blocksize, size)

        # Download starts, ends or an update of the progress bar is needed:
        if progress == 0 or progress == 1 \
           or time.time() > self._last_hook["time"] + self.update_intervall:
            self._download_in_progress(blocks, blocksize, size)

        # Download is complete
        if progress == 1:
            self._download_finished(blocks, blocksize, size)
        return None

    
if __name__ == "__main__":
    myhook = Reporthook(
        url="http://www.eso.org/public/archives/images/publicationtiff10k/eso1242a.tif",
        target="milky_way.tif"
        )    
    urllib.request.urlretrieve(myhook.url, myhook.target, myhook)
