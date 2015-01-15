#!/bin/bash
### BEGIN INIT INFO
# Provides:          EMSM - extendable minecraft server manager
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Starts and stops your minecraft worlds.
### END INIT INFO

EMSM=`which minecraft`
PLUGIN=initd

test -x $EMSM || exit 0

case "$1" in
   start)
      $EMSM $PLUGIN --start
      ;;
   stop)
      $EMSM $PLUGIN --stop
      ;;
   restart)
      $EMSM $PLUGIN --restart
      ;;
   status)
      $EMSM $PLUGIN --status
      ;;
   *)
      echo "Usage: $0 {start|stop|restart|status}" >&2
      exit 1
      ;;
esac
