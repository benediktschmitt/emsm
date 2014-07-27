.. _contribute:   
   
Contribute
==========

.. image:: /_static/logo/octocat_small.png
   :height: 40
   :align: right

**This project needs your help!**
Please help to improve this application and fork the repository on
`GitHub. <https://github.com/benediktschmitt/emsm>`_

Bug reports
-----------

When you found a bug, please create a bug report on 
`GitHub/Issues. <https://github.com/benediktschmitt/emsm/issues>`_
The EMSM logs all uncatched exceptions with a traceback in the log file.
Please attach the section, that contains the corresponding traceback to the bug 
report.
If you know how to fix the bug, you're welcome to send a *pull request.*

Code
----

If you like the EMSM and you want to contribute to the code, then do it :)

Usually, the *dev* branch is ahead of the *master* branch and commits should
always go to *dev*.

Plugins
-------

You wrote a new plugin, great. Create a request on GitHub and I will add it to
the plugins list.

To simplify the usage of your plugin, you could prepare the plugin in the
following ways:

#. Choose a short and unique name for your plugin.
#. Create a :mod:`plugin package <plugins>`, that contains the source file and
   the data that comes with your plugin.
#. Add a small `reST <http://sphinx-doc.org/>`_ docstring to your plugin.
   If you don't know how to do this, you can take a look at the source code 
   of some other plugins.
   The documentation should at least contain the following sections to be
   useful:
  
   * About (What does your plugin?)
   * Download URL
   * Configuration
   * Arguments

Spelling Mistakes
-----------------

I guess this documentation and the source code contains a lot of spelling
mistakes. Please help to reduce them.