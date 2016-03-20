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
    url = "https://voidptr.uk/projects/surrect.html",
    packages=["surrect"],
    scripts=["bin/surrect"]
)

