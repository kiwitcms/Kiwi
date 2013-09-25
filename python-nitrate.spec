Name: python-nitrate
Version: 0.10
Release: 0%{?dist}

Summary: Python API for the Nitrate test case management system
Group: Development/Languages
License: LGPLv2

URL: http://psss.fedorapeople.org/python-nitrate/
Source0: http://psss.fedorapeople.org/python-nitrate/%{name}-%{version}.tar.bz2

BuildArch: noarch
BuildRequires: python-devel
Requires: python-kerberos

%description
python-nitrate is a Python interface to the Nitrate test case
management system. The package consists of a high-level Python
module (provides natural object interface), a low-level driver
(allows to directly access Nitrate's XMLRPC API) and a command
line interpreter (useful for fast debugging and experimenting).

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{python_sitelib}/nitrate
install -pm 755 source/nitrate %{buildroot}%{_bindir}
install -pm 644 source/*.py %{buildroot}%{python_sitelib}/nitrate
install -pm 644 documentation/*.1.gz %{buildroot}%{_mandir}/man1

%files
%{_mandir}/man1/*
%{_bindir}/nitrate
%{python_sitelib}/*
%doc COPYING README examples

%changelog
* Mon Dec 10 2012 Petr Šplíchal <psplicha@redhat.com> 0.9-0
- New function unlisted() for conversion from human readable list
- Clean up the cache before testing caching
- Fix test plan initialization by type name
- Rename test case components container to CaseComponents
- Implemented TestPlan.children property [BZ#863226]
- Allow to select cases when creating a new run [BZ#863480]
- Invalid category should raise Nitrate exception [BZ#862523]
- Implement PlanType using XMLRPC instead of hard coded values [BZ#841299]
- Cleanup of log, cache and color funtions
- Use unicode for logging where necessary [BZ#865033]
- Use unicode for logging in _setter() [BZ#865033]
- Sane unicode representation for user with no name [BZ#821629]
- Support for system-wide config in /etc/nitrate.conf [BZ#844363]
- Remove *.pyc files as well when cleaning
- Move global variables out of the functions
- Move utils tests into a separate class
- Document how to get a short Nitrate summary [BZ#883798]
- Push files to the production web only when in the master branch
- New TestCase reference link field [BZ#843382]
- Forgotten 'notes' in the list of test case attributes
- Don't forget to include errata id when creating a new test run
- Fix test run errata update, improve the self test
- Added errata field in class TestRun
- Suggest https in the minimal config example
- Test case automation flags cleanup
- Empty script or arguments to be handled same as None
- Smarter implementation of the listed() function

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8-1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Feb 29 2012 Petr Šplíchal <psplicha@redhat.com> - 0.8-0
- New method clear() for cleaning containers
- Component and Components class implementation
- Improved object initialization and id check

* Wed Feb 22 2012 Petr Šplíchal <psplicha@redhat.com> - 0.7-2
- Fix url, directory ownership and preserve timestamps.

* Wed Feb 22 2012 Petr Šplíchal <psplicha@redhat.com> 0.7-1
- Initial packaging.
