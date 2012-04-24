#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='StatusBoard',
    version='2.0',
    packages=find_packages(),
    package_data={
        'StatusBoard': [
            'templates/*.html', 'static/weather-icons/*.png', 'static/*.js',
            'static/*.css', 'static/gfx/*.png', 'static/gfx/*.jpg', 'static/gfx/*.css'
        ]
    },
    install_requires=[
        'tornado==2.1', 'sleekxmpp==1.0rc2'
    ],
    entry_points={
        'console_scripts': [
            'status_board=StatusBoard.scripts.status_board:main',
            'status_board_setup_db=StatusBoard.scripts.setup_db:main'
        ]
    },
    zip_safe=False
)