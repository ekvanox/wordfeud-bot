#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup for wordfeudbot."""

from setuptools import setup
import os

setup(
    name='wordfeudbot',
    version='',  # Set new version
    author="Pricehacker",
    author_email="admin@system.gq",
    description="A python script that automates the game of wordfeud",
    url="https://github.com/Pricehacker/wordfeud-bot",
    license='MIT',
    include_package_data=True,
    packages=["wordfeudbot", "wordfeudbot/wordfeud_logic"],
    entry_points={
        "console_scripts": [
            "wordfeudbot = wordfeudbot.main:main",
        ]
    },
    install_requires=[            # I get to this in a second
        'coloredlogs',
        'emoji',
        'requests',
        'urllib3',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
