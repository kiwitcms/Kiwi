# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def get_version():
    return open('VERSION.txt', 'r').read().strip('\r\n')


PACKAGE_NAME = 'nitrate'
PACKAGE_VER = get_version()
PACKAGE_DESC = 'Test Case Management System'
PACKAGE_URL = 'https://fedorahosted.org/nitrate/wiki'


def get_files_below(path):
    # we need to generate a list of paths to static files
    # We have been invoked from "build".
    # The files we need are in "build/tcms/static"
    # The paths must be relative to "tcms"
    # Therefore we add a "tcms" to os.walk, and strip off the leading "tcms" at
    # the end:
    for (dirpath, dirnames, filenames) in os.walk(os.path.join('tcms', path)):
        for filename in filenames:
            # strip off leading "tcms/" string from each path:
            yield os.path.join(dirpath, filename)[5:]


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
    name=PACKAGE_NAME,
    version=PACKAGE_VER,
    description=PACKAGE_DESC,
    url=PACKAGE_URL,
    license='GPLv2+',
    packages=find_packages(exclude='tests'),
    # package_data=get_package_data(),
    install_requires=install_requires,
    dependency_links=dependency_links,
    include_package_data=True,
)
