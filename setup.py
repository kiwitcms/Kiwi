# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def get_version():
    return open('VERSION.txt', 'r').read().strip('\r\n')


def get_package_data():
    # annoyingly, it appears that package_data has to list filenames; it can't
    # cope with directories, so we have to figure this out for it:
    result = {
        '': [] + list(get_files_below('../templates'))
               + list(get_files_below('../static'))
               + list(get_files_below('../docs')),
    }
    return result


def get_install_requires():
    requires = []
    links = []
    for line in open('requirements/base.txt', 'r'):
        line = line.strip()
        parts = line.split('#egg=')
        if len(parts) == 2:
            links.append(line)
            requires.append(parts[1])
        else:
            requires.append(line)
    return requires, links

install_requires, dependency_links = get_install_requires()


setup(
    name='nitrate',
    version=get_version(),
    description='Test Case Management System',
    author='Nitrate Team',
    maintainer='Chenxiong Qi',
    maintainer_email='qcxhome@gmail.com',
    url='https://github.com/Nitrate/Nitrate/',
    license='GPLv2+',
    packages=find_packages(),
    # package_data=get_package_data(),
    install_requires=install_requires,
    dependency_links=dependency_links,
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ]
)
