.. _changelog:

Changelog
=========

This log contains only the changes beginning with version *3.1.1-beta*.

* 3.1.1-beta - 3.2.2-beta

  * added :meth:`emsm.server.BaseServerWrapper.world_address` method
  * added :meth:`emsm.server.BaseServerWrapper.log_error_re` method
  * added *termcolor* as Python requirement
  * added *colorama* as Python requirement
  * added *pyyaml* as Python requirement
  * added *wait_check_time* parameter to :meth:`emsm.worlds.WorldWrapper.start`
  * updated the console output: the output is now sorted, colored and consistent
  * updated :mod:`plugins.guard` plugin (big rework, take a look)
