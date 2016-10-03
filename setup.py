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
# -----------------------------------------------

# std
from setuptools import setup

# local
try:
    import emsm
except ImportError:
    emsm = None


# Setup
# -----------------------------------------------

long_description = open("README.rst").read()

requirements = [
    line.strip()
    for line in open("emsm/requirements.txt")
    if line.strip()
    ]

version = emsm.core.VERSION if emsm else "- n/a -"

setup(
    name = "emsm",
    version = version,
    url = "https://github.com/benediktschmitt/emsm",
    license = "MIT License",
    author = "Benedikt Schmitt",
    author_email = "benedikt@benediktschmitt.de",
    description = "A lightweight, easy to extend mineraft server manager",
    long_description = long_description,
    packages = ["emsm", "emsm.core", "emsm.core.lib", "emsm.plugins"],
    include_package_data = True,
    platforms = "LINUX",
    install_requires = requirements,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.2",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities"
    ]
)
