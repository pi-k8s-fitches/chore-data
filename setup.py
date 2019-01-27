#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name="nandy-data",
    version="0.1",
    packages=["nandy", "nandy.store"],
    package_dir={'':'lib'},
    install_requires=[
        "redis==2.10.6",
        "PyMySQL==0.9.3",
        "SQLAlchemy==1.2.15",
        "SQLAlchemy-JSONField==0.7.1",
        "flask_jsontools==0.1.1-0",
        "graphyte==1.5"
    ]
)