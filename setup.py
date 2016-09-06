#!/usr/bin/env python3
from os import path
from setuptools import setup, find_packages

with open(path.join("surrect", "meta.py")) as fp:
    exec(fp.read(), globals(), locals())

setup(
    name = "surrect",
    version = __version__,
    author = "Elliot Thomas",
    author_email = "elliot@voidptr.uk",
    description = "An extendible static site generator.",
    license = "MIT",
    url = "https://voidptr.uk/projects/surrect.html",
    classifiers = [
        "Environment :: Console",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License"
    ],
    packages=["surrect", "surrect.scroll"],
    scripts=["bin/surrect"],
)

