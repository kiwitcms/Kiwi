Name: python-nitrate
Version: 0.7
Release: 1%{?dist}

Summary: Python API for the Nitrate test case management system
Group: Development/Languages
License: LGPLv2

URL: http://psss.fedorapeople.org/python-nitrate/
Source0: http://psss.fedorapeople.org/python-nitrate/%{name}-%{version}.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

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

%clean
rm -rf %{buildroot}

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{python_sitelib}/nitrate
install -m 755 source/nitrate %{buildroot}%{_bindir}
install -m 644 source/*.py %{buildroot}%{python_sitelib}/nitrate
install -m 644 documentation/*.1.gz %{buildroot}%{_mandir}/man1

%files
%defattr(-,root,root,-)
%{_mandir}/man1/*
%{_bindir}/nitrate
%{python_sitelib}
%doc COPYING README examples

%changelog
* Wed Feb 22 2012 Petr Splichal <psplicha@redhat.com> 0.7-1
- Initial packaging.
