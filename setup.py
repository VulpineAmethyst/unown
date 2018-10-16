#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='Unown',
    version='0.1.0dev',
    python_requires='>=3.7.0',
    install_requires=[
        'lxml>=2.0',
        'beautifulsoup4>=4.0.0',
        'tomlkit>=0.4.0',
        'jinja2>=2.0'
    ],
    packages=find_packages(),
    package_data={
        'unown': ['templates/*']
    },
    scripts=[
        'unown.py',
        'contrib/extract_4chan.py',
        'contrib/merge_4chan.py'
    ],
    author='Kiyoshi Aman',
    author_email='kiyoshi.aman@gmail.com',
    description='An EPUB 3.0-compliant epub generator',
    license='AGPL-3.0+',
    keywords='epub epub3 epub3.0 python3 python3.7',
    url='https://git.aerdan.org/Aerdan/unown'
)
