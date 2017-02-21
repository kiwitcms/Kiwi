# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

import tcms


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
    with open('requirements/base.txt', 'r') as f:
        for line in f:
            dep_line = line.strip()
            parts = dep_line.split('#egg=')
            if len(parts) == 2:
                links.append(dep_line)
                requires.append(parts[1])
            else:
                requires.append(dep_line)
        return requires, links

install_requires, dependency_links = get_install_requires()


def get_long_description():
    with open('README.rst', 'r') as f:
        return f.read()


setup(
    name='nitrate',
    version=tcms.VERSION,
    description='Test Case Management System',
    long_description=get_long_description(),
    author='Nitrate Team',
    maintainer='Chenxiong Qi',
    maintainer_email='qcxhome@gmail.com',
    url='https://github.com/Nitrate/Nitrate/',
    license='GPLv2+',
    keywords='test case',

    install_requires=install_requires,
    dependency_links=dependency_links,

    packages=find_packages(),
    include_package_data=True,
#    data_files=[
#        ('/etc/httpd/conf.d/', ['contrib/conf/nitrate-httpd.conf']),
#        ('/etc/init.d', ['contrib/script/celeryd']),
#        ],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
