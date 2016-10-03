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


# Modules
# ------------------------------------------------

# std
import logging
import logging.handlers
import os
import queue


# ...
# ------------------------------------------------

__all__ = [
    "Logger"
    ]


# Classes
# ------------------------------------------------
class Logger(object):
    """
    Sets the *root* :class:`logging.Logger` up.

    The EMSM logger queues all log records until the :file:`emsm.log` can be
    acquired without side effects. This is the case, when the
    :class:`~emsm.core.application.Application` acquired the *file lock*.
    The queued records are then pushed to the :file:`emsm.log`.

    The EMSM logging stategy requires, that each module uses its own
    logger instance:

    .. code-block:: python

        >>> import logging
        >>> log = logging.getLogger(__file__)
    """

    def __init__(self, app):
        """
        """
        self._app = app
        self._log_dir = app.paths().logs()

        # The root logger
        self._root_log = logging.getLogger()
        self._root_log.setLevel(logging.INFO)

        # The EMSM log format.
        self._log_format = logging.Formatter(
            fmt="[{asctime}][{levelname:8}][{module:25}] {message}",
            datefmt="%Y-%m-%d %H:%M:%S", style="{"
            )

        # Used to store the log records until we can access the *emsm.log*.
        # As soon as *emsm.log* is opened, we write all records in the queue
        # to the log file.
        # These attributes are set to None, as soon as the log file is opened.
        self._log_queue = queue.Queue()
        self._log_queue_handler = logging.handlers.QueueHandler(self._log_queue)
        self._root_log.addHandler(self._log_queue_handler)

        # The FileHandler for the EMSM log file (usually *emsm.log*)
        # The file is opened, as soon as the Application acquired the file lock.
        #
        # See also:
        #   * setup()
        self._log_file_handler = None
        return None

    def setup(self):
        """
        Opens the :file:`emsm.log` and pushes all queued log recods to the log
        file.

        .. hint::

            This method requires that the Application aquired the file lock.
        """
        # We use the rotating file handler so that the logfiles are
        # automatically compressed, when they are bigger than 10mb.
        self._log_file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self._log_dir, "emsm.log"),
            maxBytes = 10*1024**2,
            backupCount = 5
            )
        self._log_file_handler.setFormatter(self._log_format)

        # Push the queued records to the file handler.
        while not self._log_queue.empty():
            record = self._log_queue.get(block=False)
            self._log_file_handler.handle(record)

        # Add the file handler to the root logger and remove the queue handler.
        self._root_log.addHandler(self._log_file_handler)

        self._root_log.removeHandler(self._log_queue_handler)
        self._log_queue_handler = None
        self._log_queue = None
        return None
