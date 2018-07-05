Name: waldur-ansible
Summary: Ansible plugin for Waldur
Group: Development/Libraries
Version: 0.6.1
Release: 1.el7
License: MIT
Url: http://waldur.com
Source0: %{name}-%{version}.tar.gz

Requires: waldur-core >= 0.161.4
Requires: waldur-openstack >= 0.43.4
Requires: python-passlib >= 1.7.0

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

%description
Ansible plugin for Waldur.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{python_sitelib}/*

%changelog
* Sat May 12 2018 Jenkins <jenkins@opennodecloud.com> - 0.6.1-1.el7
- New upstream release

* Sun Apr 8 2018 Jenkins <jenkins@opennodecloud.com> - 0.5.2-1.el7
- New upstream release

* Wed Mar 28 2018 Jenkins <jenkins@opennodecloud.com> - 0.5.1-1.el7
- New upstream release

* Tue Mar 27 2018 Jenkins <jenkins@opennodecloud.com> - 0.5.0-1.el7
- New upstream release

* Tue Mar 6 2018 Jenkins <jenkins@opennodecloud.com> - 0.4.0-1.el7
- New upstream release

* Fri Dec 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.3-1.el7
- New upstream release

* Mon Nov 20 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.2-1.el7
- New upstream release

* Fri Oct 20 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.1-1.el7
- New upstream release

* Tue Oct 10 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.0-1.el7
- New upstream release

* Sat Sep 16 2017 Jenkins <jenkins@opennodecloud.com> - 0.2.0-1.el7
- New upstream release

* Tue Jul 25 2017 Jenkins <jenkins@opennodecloud.com> - 0.1.0-1.el7
- New upstream release
