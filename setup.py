# pylint: disable=missing-docstring

from setuptools import find_packages, setup

import tcms


def get_install_requires(path):
    requires = []
    links = []

    with open(path, "r") as file:
        for line in file:
            if line.startswith("-r "):
                continue

            dep_line = line.strip()
            parts = dep_line.split("#egg=")
            if len(parts) == 2:
                links.append(dep_line)
                requires.append(parts[1])
            else:
                requires.append(dep_line)
        return requires, links


INSTALL_TARBALLS, DEPENDENCY_TARBALLS = get_install_requires(
    "requirements/tarballs.txt"
)
INSTALL_BASE, DEPENDENCY_BASE = get_install_requires("requirements/base.txt")
INSTALL_REQUIRES = INSTALL_TARBALLS + INSTALL_BASE
DEPENDENCY_LINKS = DEPENDENCY_TARBALLS + DEPENDENCY_BASE


def get_long_description():
    with open("README.rst", "r") as file:
        return file.read()


setup(
    name="kiwitcms",
    version=tcms.__version__,
    description="Test Case Management System",
    long_description=get_long_description(),
    maintainer="Kiwi TCMS",
    maintainer_email="info@kiwitcms.org",
    url="https://github.com/kiwitcms/Kiwi/",
    license="GPLv2",
    keywords="test case",
    install_requires=INSTALL_REQUIRES,
    dependency_links=DEPENDENCY_LINKS,
    packages=find_packages(exclude=["kiwi_lint*", "*.tests", "tcms.settings.test"]),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
