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
Please attach the log file section that contains the traceback of the
exception if possible. You can find the log at ``EMSM_ROOT/logs/emsm.log``.
If you know how to fix the bug, you're welcome to send a *pull request.*

Code
----

If you like the EMSM and want to contribute to the code, then do it :)

Note, that the *dev* branch is usually ahead of the *master* branch and commits 
should always go to *dev*.

Plugins
-------

You wrote a new plugin? Great! Write me about it on GitHub and I will add it to the
plugins list.

To simplify the usage of your plugin, you could prepare the plugin in the
following ways:

#. Choose a short and unique name for your plugin.
#. Create a :mod:`plugin package <plugins>`, that contains the source file and
   the data that comes with your plugin.
#. Add a small `reST <http://sphinx-doc.org/>`_ docstring to your plugin.
   If you don't know how to do this, you can take a look at the source code 
   of some other plugins. It's quite easy.
   
   A useful documentation contains at least the following sections:
  
   * About (What does your plugin?)
   * Download URL
   * Configuration
   * Arguments

Spelling Mistakes
-----------------

I guess the source code and this documentation contain a lot of spelling
mistakes. Please help to reduce them.