# pylint: disable=missing-docstring

from setuptools import setup, find_packages

import tcms


def get_install_requires():
    requires = []
    links = []
    with open('requirements/base.txt', 'r') as file:
        for line in file:
            dep_line = line.strip()
            parts = dep_line.split('#egg=')
            if len(parts) == 2:
                links.append(dep_line)
                requires.append(parts[1])
            else:
                requires.append(dep_line)
        return requires, links


INSTALL_REQUIRES, DEPENDENCY_LINKS = get_install_requires()


def get_long_description():
    with open('README.rst', 'r') as file:
        return file.read()


setup(
    name='kiwitcms',
    version=tcms.__version__,
    description='Test Case Management System',
    long_description=get_long_description(),
    author='various',
    maintainer='Kiwi TCMS',
    maintainer_email='info@kiwitcms.org',
    url='https://github.com/kiwitcms/Kiwi/',
    license='GPLv2+',
    keywords='test case',

    install_requires=INSTALL_REQUIRES,
    dependency_links=DEPENDENCY_LINKS,

    packages=find_packages(),
    include_package_data=True,

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
