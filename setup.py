# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('VERSION.txt', 'r') as f:
    pkg_version = f.read().strip()


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
    version=pkg_version,
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

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
