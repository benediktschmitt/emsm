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


# Modules
# ------------------------------------------------

# std
import os
import sys


# Data
# ------------------------------------------------

DOC_SRC = os.path.dirname(__file__)
EMSM_ROOT = os.path.abspath(os.path.join("../../"))

# Make sure the EMSM packages are found by autodoc.
sys.path.insert(0, EMSM_ROOT)


# Classes
# ------------------------------------------------

class BaseDocGenerator(object):
    """
    """

    def __init__(self, source_dir, doc_dir, automodule_conf=None):
        """
        """
        self._source_dir = source_dir
        self._doc_dir = doc_dir

        if automodule_conf is None:
            automodule_conf = list()
        self._automodule_conf = automodule_conf
        return None

    def _list_module_paths(self):
        """
        """
        raise NotImplemented()
    
    def _generate_rst_file(self, module):
        """
        """
        tmp = (":mod:`{module}`",
               "="*(9 + len(module)),
               "",
               ".. automodule:: {module}",
               
               ""
               )
        tmp = "\n".join(tmp)
        tmp = tmp.format(module=module)

        module_name = module[module.rfind(".") + 1:]
        
        doc_filename = module_name if module_name != "index" else "index_"
        doc_filename += ".rst"
        
        with open(os.path.join(self._doc_dir, doc_filename), "w") as file:

            print(":mod:`{}`".format(module), file=file)
            print("="*(9+len(module)), file=file)
            print("", file=file)
            print(".. automodule:: {}".format(module), file=file)
            for option in self._automodule_conf:
                print("   :{}:".format(option), file=file)
        return None
                  
    def _update(self):
        """
        """
        modules = self._list_module_paths()
        for module in modules:
            self._generate_rst_file(module)
        return None

    def _clear(self):
        """
        Removes all *.rst* files in *self._doc_dir* except
        the *index.rst* file.
        """
        for filename in os.listdir(self._doc_dir):
            if not filename.endswith(".rst"):
                continue
            if filename == "index.rst":
                continue
            os.remove(os.path.join(self._doc_dir, filename))
        return None

    def run(self):
        """
        """
        self._clear()
        self._update()
        return None
                  

class PluginDocGenerator(BaseDocGenerator):
    """
    """

    def _list_module_paths(self):
        """
        """
        def is_plugin(path):
            """
            """
            filename = os.path.basename(path)
            if not path:
                return False
            if not os.path.isfile(path):
                return False
            if not path.endswith(".py"):
                return False
            if not filename[0].isalnum():
                return False
            return True

        modules = list()
        for filename in os.listdir(self._source_dir):
            path = os.path.join(self._source_dir, filename)
            if not is_plugin(path):
                continue
            
            module_name = filename[:filename.find(".")]
            module_path = "plugins." + module_name
            modules.append(module_path)
        return modules


class APIDocGenerator(BaseDocGenerator):
    """
    """

    def __init__(self, source_dir, doc_dir):
        """
        """
        super().__init__(
            source_dir,
            doc_dir,
            ["members", "undoc-members", "show-inheritance"]
            )
        return None

    def _list_module_paths(self):
        """
        """
        def is_python_file(path):
            """
            """
            filename = os.path.basename(path)
            if not path:
                return False
            if not os.path.isfile(path):
                return False
            if not path.endswith(".py"):
                return False
            if not filename[0].isalnum():
                return False
            return True
        
        modules = list()
        for filename in os.listdir(self._source_dir):
            path = os.path.join(self._source_dir, filename)
            if not is_python_file(path):
                continue
            
            module_name = filename[:filename.find(".")]
            module_path = "emsm." + module_name
            modules.append(module_path)
        return modules


# Main
# ------------------------------------------------

def main():
    """
    """
    # Generate the documentation for the plugins.
    plugin_doc_gen = PluginDocGenerator(
        os.path.join(EMSM_ROOT, "plugins"),
        os.path.join(DOC_SRC, "plugins")
        )
    plugin_doc_gen.run()

    api_doc_gen = APIDocGenerator(
        os.path.join(EMSM_ROOT, "emsm"),
        os.path.join(DOC_SRC, "api")
        )
    api_doc_gen.run()
    return None
