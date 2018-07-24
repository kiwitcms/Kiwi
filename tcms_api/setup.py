#!/usr/bin/env python
# coding: utf-8
# pylint: disable=missing-docstring
from setuptools import setup


with open("README.rst") as readme:
    LONG_DESCRIPTION = readme.read()


setup(name='tcms-api',
      version='5.0',
      packages=['tcms_api'],
      package_dir={'tcms_api': '.'},
      description='Python API for the Kiwi TCMS test case management system',
      long_description=LONG_DESCRIPTION,
      author='Petr Šplíchal',
      author_email='psplicha@redhat.com',
      maintainer='Kiwi TCMS',
      maintainer_email='info@kiwitcms.org',
      license='LGPLv2+',
      url='https://github.com/kiwitcms/Kiwi/tree/master/tcms_api',
      python_requires='>=3.6',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU Lesser General Public License v2' +
          ' or later (LGPLv2+)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
      ])
