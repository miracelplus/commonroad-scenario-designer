#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

setup_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{setup_dir}/README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="commonroad-scenario-designer",
    version="0.2",
    description="Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Technical University of Munich",
    author_email="commonroad@lists.lrz.de",
    url="https://commonroad.in.tum.de/",
    license="GNU General Public License v3.0",
    packages=find_packages(exclude=("test", "ci", "files", "docs", "tutorials")),
    include_package_data=True,
    install_requires=[
        "numpy>=1.16.4",
        "lxml>=4.3.4",
        "commonroad-io>=2020.2",
        "pyproj>=2.2.0",
        "scipy>=1.3.0",
        "Pillow >= 7.1.1",
        "mercantile >= 1.1.3",
        "utm >= 0.5.0",
        "cartopy >= 0.17.0",
        "PyQt5>=5.12.2",
        "matplotlib>=3.1.0",
        "ordered-set>=4.0.2"
    ],
    extras_require={"GUI": ["matplotlib>=3.1.0"]},
    python_requires=">=3.6",
    entry_points={"console_scripts": ["crdesigner=crdesigner.io.command_line:main"]},
)
