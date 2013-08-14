#!/usr/bin/env python3


# Modules
# --------------------------------------------------
import urllib.request
import os
import shutil
import shlex


# Data
# --------------------------------------------------
__all__ = ["ServerError", "ServerUpdateFailure",
           "ServerStatusError", "ServerIsOnlineError",
           "ServerIsOfflineError", "BaseServerWrapper"
           ]


# Backward compatibility
# --------------------------------------------------
if not hasattr(shlex, "quote"):
    # From the Python3.3 library
    import re
    _find_unsafe = re.compile(r'[^\w@%+=:,./-]', re.ASCII).search
    def _shlex_quote(s):
        """Return a shell-escaped version of the string *s*."""
        if not s:
            return "''"
        if _find_unsafe(s) is None:
            return s

        # use single quotes, and put single quotes into double quotes
        # the string $'b is then quoted as '$'"'"'b'
        return "'" + s.replace("'", "'\"'\"'") + "'"
    shlex.quote = _shlex_quote
    del re
    
if hasattr(shutil, "which"):
    _JAVA = shutil.which("java")
else:
    _JAVA = "java"

try:
    FileNotFoundError
except:
    FileNotFoundError = OSError


# Exceptions
# --------------------------------------------------
class ServerError(Exception):
    """ Base class for all module exceptions. """
    pass


class ServerUpdateFailure(ServerError):
    """
    Raised if the update of a server failed.
    """

    def __init__(self, server):
        self.server = server
        return None

    def __str__(self):
        temp = "The update of the server '{}' failed."\
               .format(self.server.name)
        return temp

    
class ServerStatusError(ServerError):
    """
    Raised if the server should be online/offline
    for an action but is offline/online.
    """

    def __init__(self, server, status, msg = str()):
        self.server = server
        self.status = status
        self.msg = msg
        return None

    def __str__(self):
        if self.status:
            temp = "The server '{}' is online. {}"
        else:
            temp = "The server '{}' is offline. {}"
        temp = temp.format(self.server.name, self.msg)
        return temp    


class ServerIsOnlineError(ServerStatusError):
    """
    Raised if the server is online but should be offline.
    """
    
    def __init__(self, server, msg = str()):
        ServerStatusError.__init__(self, server, True, msg)
        return None

    
class ServerIsOfflineError(ServerStatusError):
    """
    Raised if the server is offline but should be online.
    """

    def __init__(self, server, msg = str()):
        ServerStatusError.__init__(self, server, False, msg)
        return None

    
# Classes
# --------------------------------------------------
class BaseServerWrapper(object):    
    """
    Wraps a minecraft server (file).

    """
       
    def __init__(self,
                 server,
                 url,
                 start_args="",
                 name=None,
                 auto_install=True
                 ):
        """ ============ ===========================================
            parameter    description
            ============ ===========================================
            server       The path of the server.
            url          The download url of the server.
            start_args   The mojang minecraft server needs: "nogui."
            name         The name of the server in the application.
            auto_install Downloads the server-file if not yet done.
            ============ ===========================================
        """
        if name is None:
            name = os.path.basename(server)
            
        self.server = server
        self.name = name
        self.url = url
        self.start_args = start_args

        # Download the server if not yet done.
        if auto_install and not os.path.exists(self.server):
            self.update()
        return None

    def is_online(self):
        """
        Returns false per default.
        
        Should be overwritten.
        """
        return False    
    
    def get_start_cmd(self, init_ram, max_ram):
        """
        Returns the command to start the server.

        init_ram is the initial size of the memory allocation pool
        for the server and max_ram the maximum size.        
        """
        global _JAVA
        
        if max_ram < init_ram:
            init_ram, max_ram = max_ram, init_ram
            
        cmd = "{java} -Xms{init_ram}M -Xmx{max_ram}M -jar {server} {start_args}"
        cmd = cmd.format(
            java=_JAVA,
            init_ram=init_ram,
            max_ram=max_ram,
            server=shlex.quote(self.server),
            start_args=self.start_args
            )
        return cmd

    def update(self, reporthook=None):
        """
        Downloads the server_jar into a temporary file and copies the
        file if the download succeeded to the server directory.
        reporthook is the reporthook of urllib.request.urlretrieve.

        Raises: ServerIsOnlineError
        Raises: ServerUpdateFailure
        """
        if self.is_online():
            raise ServerIsOnlineError(self)

        try:
            temp_server_file, http_message = urllib.request.urlretrieve(
                self.url,
                reporthook=reporthook
                )
        except (OSError, urllib.error.URLError):
            raise ServerUpdateFailure(self)
        else:
            shutil.move(temp_server_file, self.server)
        return None    

    def uninstall(self):
        """
        Removes the server file.

        Raises: ServerIsOnlineError
        """
        if self.is_online():
            raise ServerIsOnlineError(self)
        
        try:
            os.remove(self.server)
        except FileNotFoundError:
            pass
        return None
