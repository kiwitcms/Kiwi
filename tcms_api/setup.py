#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

# Prepare short and long description
description = 'Python API for the Kiwi TCMS test case management system'
with open("README.rst") as readme:
    long_description = readme.read()


setup(name='tcms-api',
      version='4.2',
      packages=['tcms_api'],
      package_dir={'tcms_api': '.'},
      scripts=['tcms'],
      description=description,
      long_description=long_description,
      author='Petr Šplíchal',
      author_email='psplicha@redhat.com',
      maintainer='Kiwi TCMS',
      maintainer_email='info@kiwitcms.org',
      license='LGPLv2+',
      url='https://github.com/kiwitcms/Kiwi/tree/master/tcms_api',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU Lesser General Public License v2' +
          ' or later (LGPLv2+)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
      ])
