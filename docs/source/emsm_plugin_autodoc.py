#!/usr/bin/python3

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

"""
About
-----

Generates simple .rst files, so that autodoc can generate the documentation for
the plugins.

THIS MODULE WILL ADD PATHS TO sys.path!

THIS MODULE IS EXECUTED, WHEN IMPORTED!

Example
-------

When the .rst file for the *backups.py* plugin module is created, it results in
this text::

   :mod:``backups``
   ================

   .. module:: backups

   .. automodule:: backups

The rest is done by *autodoc*.
"""


# Modules
# ------------------------------------------------
import os
import sys


# Data and configuration
# ------------------------------------------------

# The directory of this script (and the source directory of the documentation)
DOC_SRC = os.path.dirname(__file__)

# The directory of the documentation files for the 'normal' plugins and the
# core plugins.
DOC_PLUGINS_DIR = os.path.join(DOC_SRC, "plugins")
DOC_CORE_PLUGINS = os.path.join(DOC_SRC, "core_plugins")

# The EMSM root directory is two directories above in the directory tree.
EMSM_ROOT = os.path.abspath(os.path.join(DOC_SRC, "../../"))

# We scan these paths for plugins. Note, that the paths may point to
# directories or files. Every file, that is a Python module (.py) is
# considered to be an EMSM plugin.
PLUGIN_SEARCH_PATHS = [os.path.join(EMSM_ROOT, "plugins")]

# These plugins are treated as *core plugins* and their .rst file is
# generated in *core_plugins* instead of *plugins*.
CORE_PLUGINS = ["backups", "guard", "initd", "plugins", "server",
                "status", "worlds"]


# Functions
# ------------------------------------------------

# First of all, we add the search paths to Python's include path, so that
# we can find the modules.
# We also add the EMSM/application path, to avoid ImportErrors when the
# plugin modules are included (otherwise, they can't include emsm modules).
sys.path.append(os.path.join(EMSM_ROOT, "emsm"))
sys.path.extend(PLUGIN_SEARCH_PATHS)

def list_plugins(search_path):
    """
    If *path* points to a file, the returned list contains the *path* if
    it is a valid EMSM plugin.

    If *path* points to a directy, the returned list contains all valid
    emsm plugins in that directory.
    """
    # Todo: Extend the emsm plugin_manager to be able to load and validate
    #       plugins without a running emsm application.
    #       So we can avoid duplicate code and a better determination of Python
    #       modules that are plugins and those that are not.
    def is_plugin_filename(path):
        filename = os.path.basename(path)
        if os.path.isdir(path):
            return False
        elif filename.startswith("_"):
            return False
        elif not filename.endswith(".py"):
            return False
        elif filename.count(".") != 1:
            return False
        return True
    
    plugin_paths = [path for path in os.listdir(search_path) \
                    if is_plugin_filename(path)]
    return plugin_paths

def generate_rst_file(plugin_path):
    """
    Generates the .rst file for the plugin at that path.
    """
    # The plugin name is the filename without extensions.
    plugin_name = os.path.basename(plugin_path)
    plugin_name = plugin_name[0:plugin_name.find(".")]

    # Create the .rst file in the correct directory.
    if plugin_name != "index":
        rst_filename = plugin_name + ".rst"
    else:
        rst_filename = "index_plugin.rst"
        
    if plugin_name in CORE_PLUGINS:
        rst_file = os.path.join(DOC_CORE_PLUGINS, rst_filename)
    else:
        rst_file = os.path.join(DOC_PLUGINS_DIR, rst_filename)

    with open(rst_file, "w") as file:
        rst_text = (":mod:`{plugin_name}`",
                    "="*(9 + len(plugin_name)),
                    "",
                    ".. automodule:: {plugin_name}"
                    )
        rst_text = "\n".join(rst_text)
        rst_text = rst_text.format(plugin_name=plugin_name)    
        file.write(rst_text)

    print("Generated '{}'.".format(rst_file))
    return None

def clean_documentation():
    """
    Removes all .rst files from a previous run in the documentation
    directories for the *plugins* and *core_plugins*.
    """
    # We only keep the index.rst file in each directory.
    for filename in os.listdir(DOC_PLUGINS_DIR):
        if filename == "index.rst":
            continue
        os.remove(os.path.join(DOC_PLUGINS_DIR, filename))
    print("Cleaned '{}'.".format(DOC_PLUGINS_DIR))

    for filename in os.listdir(DOC_CORE_PLUGINS):        
        if filename == "index.rst":
            continue
        os.remove(os.path.join(DOC_CORE_PLUGINS, filename))        
    print("Cleaned '{}'.".format(DOC_CORE_PLUGINS))
    return None

# Generate a .rst file for each plugins.
clean_documentation()
for search_path in PLUGIN_SEARCH_PATHS:
    for plugin_path in list_plugins(search_path):
        generate_rst_file(plugin_path)
