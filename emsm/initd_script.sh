#!/bin/bash
### BEGIN INIT INFO
# Provides:          EMSM - extendable minecraft server manager
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Starts and stops your minecraft worlds.
### END INIT INFO

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

EMSM=`which minecraft`
PLUGIN=initd

test -x $EMSM || exit 0
source /lib/lsb/init-functions

case "$1" in
   start)
      log_daemon_msg "Starting minecraft server" ""
      $EMSM $PLUGIN --start
      log_end_msg $?
      ;;
   stop)
      log_daemon_msg "Stopping minecraft server" ""
      $EMSM $PLUGIN --stop
      log_end_msg $?
      ;;
   restart)
      $0 stop
      $0 start
      ;;
   *)
      echo "Usage: $0 {start|stop|restart}" >&2
      exit 1
      ;;
esac
