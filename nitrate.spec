%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# Extra package build
# Documentation, define build_doc 1

Name:           nitrate
Version:        3.8.17
Release:        1%{?dist}
Summary:        Test Case Management System

Group:          Development/Languages
License:        GPLv2+
URL:            https://fedorahosted.org/nitrate/browser/trunk/nitrate
Source0:        https://fedorahosted.org/releases/n/i/nitrate/%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-setuptools

Requires:       Django = 1.8.11
Requires:       django-contrib-comments = 1.6.2
Requires:       django-celery >= 3.1.10
Requires:       django-pagination = 1.0.7
Requires:       django-tinymce = 2.3.0
Requires:       django-uuslug
Requires:       kobo-django >= 0.2.0-3
Requires:       mod_auth_kerb
Requires:       mod_ssl
Requires:       mod_wsgi >= 3.2
Requires:       MySQL-python == 1.2.5
Requires:       odfpy >= 0.9.6
Requires:       python-beautifulsoup4 >= 4.1.1
Requires:       python-kerberos
Requires:       python-qpid
Requires:       w3m

%description
Nitrate is a tool for tracking testing being done on a product.

It is a database-backed web application, implemented using Django

%if "%{build_doc}" == "1"
%package doc
Summary:        Documentation of Nitrate
Group:          Documentation
URL:            http://nitrate.readthedocs.org/en/latest/
BuildRequires:  python-sphinx >= 1.1.2

%description doc
Documentation of Nitrate
%endif

%if "%{build_apidoc}" == "1"
%package apidoc
Summary:        API documentation of Nitrate
Group:          Documentation
BuildRequires:  epydoc >= 3.0.1

%description apidoc
API documentation of Nitrate
%endif


%prep
%setup -q

# Fixup the version field in the page footer so that it shows the precise
# RPM version-release:
sed --in-place \
  -r 's|NITRATE_VERSION|%{version}-%{release}|' \
  tcms/templates/tcms_base.html


%build
%{__python} setup.py build

# Generate documentation
%if "%{build_doc}" == "1"
pushd docs
make html
popd
%endif

# Generate API documentation
%if "%{build_apidoc}" == "1"
make apidoc
%endif


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Copy static content from 32/64bit-specific python dir to shared data dir:
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{name}
mkdir -p ${RPM_BUILD_ROOT}%{_docdir}/%{name}
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{name}/static

for d in contrib; do
    cp -r ${d} ${RPM_BUILD_ROOT}%{_datadir}/%{name};
done

# Install apache config for the app:
install -m 0644 -D -p contrib/conf/nitrate-httpd.conf ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/%{name}.conf

%if "%{build_apidoc}" == "1"
# Copy apidoc to /var/www
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/www
cp -r apidoc ${RPM_BUILD_ROOT}%{_localstatedir}/www/%{name}-apidoc

# Install conf file for apidoc
install -m 0644 -D -p contrib/conf/nitrate-apidoc.conf ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/%{name}-apidoc.conf
%endif

# Celery
# Create celery log and pid dir.
install -d -m 755 ${RPM_BUILD_ROOT}%{_var}/log/celery
install -d -m 755 ${RPM_BUILD_ROOT}%{_var}/run/celery

# Install celeryd script
install -m 0755 -D -p contrib/script/celeryd ${RPM_BUILD_ROOT}%{_sysconfdir}/init.d/celeryd

%pre
# Create celery group and user
getent group celery >/dev/null || groupadd -r celery
if ! getent passwd celery >/dev/null; then
    useradd -r -g celery -G celery,nobody -d %{_var}/log/celery -s /sbin/nologin -c "TCMS celery daemons" celery
fi

%post
# Collect static file for the app:
/usr/bin/django-admin collectstatic --noinput --clear --settings=tcms.settings.product
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc0.d/K25celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc1.d/K25celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc2.d/S90celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc3.d/S90celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc4.d/S90celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc5.d/S90celeryd
ln -s %{_sysconfdir}/init.d/celeryd %{_sysconfdir}/rc6.d/K25celeryd

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog README.rst LICENSE VERSION.txt
%{python_sitelib}/tcms/
%{python_sitelib}/nitrate-%{version}-py*.egg-info/
%{_datadir}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{python_sitelib}/tcms/settings/product.py
%dir %attr(0755, celery, root) %{_var}/log/celery
%dir %attr(0755, celery, root) %{_var}/run/celery
%config(noreplace) %{_sysconfdir}/init.d/celeryd

%if "%{build_doc}" == "1"
%files doc
%defattr(-,root,root,-)
%doc docs/target/html
%endif

%if "%{build_apidoc}" == "1"
%files apidoc
%defattr(-,root,root,-)
%{_localstatedir}/www/%{name}-apidoc
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}-apidoc.conf
%endif

%changelog
* Wed Feb 11 2015 Jian Chen	<jianchen@redhat.com> 3.8.17-1
* Ignore empty string in white space character escape

* Wed Feb 11 2015 Jian Chen	<jianchen@redhat.com> 3.8.16-1
* Revert whitespace filter in run/testcaserun notes field

* Fri Jan 23 2015 Jian Chen	<jianchen@redhat.com> 3.8.15-1
* Add whitespace filter in plan/case/run text field.

* Mon Dec 22 2014 Chenxiong Qi <cqi@redhat.com> 3.8.14-1
* Specify html.parser explicitly to parse HTML document

* Thu Dec 18 2014 Chenxiong Qi <cqi@redhat.com> 3.8.13-1
- Bug fix 1174111

* Thu Dec 4 2014 Jian Chen <jianchen@redhat.com> 3.8.12-1
- Refine documents.

* Wed Oct 15 2014 Jian Chen <jianchen@redhat.com> 3.8.11-1
- Write unittest for xmlrpc methods.
- Refine documents.
- Rewrite front-end javascript with jQuery.

* Wed Aug 27 2014 Chenxiong Qi <cqi@redhat.com> 3.8.10-2
- Bug 1133483 - Unable to clone runs in TCMS
- Bug 1133912 - Script injection in notes field
- Bug 1134166 - [test plan] when user remove tag at reviewing case tag in test plan detail page, system returns 500 error

* Tue Aug 19 2014 Chenxiong Qi <cqi@redhat.com> 3.8.10-1
- Bug 1039495 - [test run][export to xml]If a case related many bugs in a run, when export the run to xml, the file only show the latest bug for this case.
- Bug 1129058 - [TestPlan |Add cases ] The browser has no response and is in dead after selecting all the selected cases
- Bug 1130903 - [xmlrpc]User can not filter case via estimated_time when invoke TestCase.filter_count method.
- Bug 1130933 - [xmlrpc] User can not update estimated_time to 0s when invoke TestRun.update method.
- Bug 1130961 - [TestPlan|Components] Can't remove all the default components of one test plan at one time
- Bug 1130966 - [xmlrpc][document] The format of estimated_time for related methods should be consistent.
- Bug 1131885 - [XML-RPC] The Texts don't trim the spaces and record them as new versions when invoking the TestCase.store_text() and TestPlan.store_text()
- TCMS-284 [Performance] Production Apache ssl_access_log report some resources(such as css,js,pic etc) can not found(HTTP 404) (RHBZ:1035958)
- TCMS-371 [Performance Test][Reporting Custom] The First Slow Query on the Top Slow Queries found on prod evn (2014-06-05 to 2014-06-12)
- TCMS-425 TestRun & TestCase estimated_time modify
- TCMS-463 [Performance]Reporting Custom Section Optimize
- TCMS-464 [Performance]Reporting Testing Report Section Optimize
- TCMS-478 [xmlrpc]Invoke TestCase.calculate_total_estimated_time with a invalid input, system returns total_estimated_time 00:00:00 not 400 error. (RHBZ:1102459)
- TCMS-480 Enable system-wide cache mechanism to support caching (RHBZ:1027589)
- TCMS-481 [xmlrpc]The result for xmlrpc method TestCase.calculate_average_estimated_time is wrong. (RHBZ:1099312)
- TCMS-482 TestPlan.update does not support 'owner' update (RHBZ:1023679)
- TCMS-484 [test run] If a run has multiple Environments, clone this run, the new run only clone the latest Environment. (RHBZ:1112561)
- TCMS-485 [xmlrpc]when invoke TestCase.link_plan method, the 404 error message lack description. (RHBZ:1112967)
- TCMS-486 [RFE] Suggest improve "Testing Report" generating for large data query (RHBZ:870384)
- TCMS-487 [RFE]: Add test case to the plan by ID (number) (RHBZ:869952)
- TCMS-488 [XMLRPC] List all the methods related to "is_active"field which all needed to be fixed (RHBZ:1108009)
- TCMS-489 [test case]A bug belongs to Run A and Run B for the same case, remove this bug from Run A in case detail page, the bug for Run B is removed as well. (RHBZ:1094603)
- TCMS-492 replace TestRun.is_current with front-end control, and remove operation code against TestRun.is_current in view
- TCMS-493 fix that two requests are emit after change a case run's status
- TCMS-494 Build base infrastructure of unit test
- TCMS-495 Optimize operations on test_case_texts
- TCMS-496 rewrite the ajax style code snippets with jquery
- TCMS-498 [TestCaseRun | Add bug] The added jira bugs don't display in the case run but actually they are added in the xml file. (RHBZ:1119666)
- TCMS-499 [DB] Fix errors when syncdb
- TCMS-500 [Cache] Cache part sections of pages
- TCMS-512 [XML-RPC] TestCase.calculate_total_estimated_time() doesn't work (RHBZ:857831)
- TCMS-513 [Performance] TCMS Reporting respond slowly and cause MySQL server high CPU usage (RHBZ:1029267)
- TCMS-514 [XML-RPC] TestCase.calculate_average_estimated_time() doesn't work (RHBZ:857830)
- TCMS-515 [TestRun][RemoveCase]Remove case into creating test run,the test run's estimated time didn't sync with its cases totally estimate time (RHBZ:849066)
- TCMS-516 [xmlrpc] Can not add cases to the runs with calling the TestRun.add_cases() method (RHBZ:1119224)
- TCMS-551 [test run] After updating the Environment value in test run detail page, user can not remove the changed environment. (RHBZ:1124210)
- TCMS-552 [xmlrpc][document] The example for TestRun.get_test_case_runs method still support is_current parameter. (RHBZ:1126398)
- TCMS-553 [Testing report] Generate testing report By Case Priority, the Priority order for different builds were different. (RHBZ:1125828)
- TCMS-554 [testing report] If all plans belongs to a product have plan tag, system display 'untagged' in tag list in testing report by Plan's Tag (RHBZ:1125815)
- TCMS-555 [Testing report] Generate testing report by Plan's Tag Per Tag View, the caserun's count for idle status was wrong. (RHBZ:1125214)
- TCMS-556 [Testing report] Generate testing report By Plan's Tag Per Tag View, the total caserun's count statistic the duplicate caseruns. (RHBZ:1125821)
- TCMS-557 [TCMS-495 | Texts]Texts of test case and test plan don't support Chinese characters (RHBZ:1126790)
- TCMS-559 [testing report] the link on Paused status in testing report generated by Case-Run Tester was wrong. (RHBZ:1126353)
- TCMS-560 [testing report] Generate testing report by Case-Run Tester, the run's count was wrong. (RHBZ:1126359)
- TCMS-569 [testing report]Generate testing report By Plan's Tag Per Tag View, click link on caserun status to access caserun list, system returns 500 error. (RHBZ:1127621)
- TCMS-570 [TCMS-487| Add cases] Make sure the cases which had been added to the plan can't be searched by case id (RHBZ:1127522)
- TCMS-571 [test case]when create case without estimated_time, system can not save the case. (RHBZ:1126322)
- TCMS-572 [xmlrpc] Do not change the content of plan's text, invoke TestPlan.store_text twice, system will save the content twice with same checksum (RHBZ:1127194)
- TCMS-573 [test plan] If clone case with Create a Copy Settings, system will go to 500 error page. (RHBZ:1126304)
- TCMS-574 [xmlrpc] Invoke TestCase.get_text to get a nonexistent version, system returns 500 error. (RHBZ:1127198)
- TCMS-575 [clone test run] The estimated time format is different with input by manual (RHBZ:1126300)
- TCMS-585 Search cases lead memory leak in production server
- TCMS-619 [XMLRPC] default_product_version is missed in the response from TestPlan
- TCMS-96 [test plan][add child node]When add child note to plan with a nonexistent plan id, the submit btn in the warning form has no effect. (RHBZ:1038950)
- TCMS-98 [test run][add bug]Add reduplicative bug to case in the run page, the content of the warning is incorrect. (RHBZ:1039408)

* Mon Aug 11 2014 Chenxiong Qi <cqi@redhat.com> 3.8.9-3
- Hotfix XMLRPC backward-compatibility broken

* Fri Aug 01 2014 Jian Chen <jianchen@redhat.com> 3.8.9-2
- TCMS-538 Solve inconsistent data of product_version field in production database.

* Thu Jul 17 2014 Jian Chen <jianchen@redhat.com> 3.8.9-1
- TCMS-376 Change Test Run product_version field to ForeignKey.
- TCMS-413 Change Optimize script field to support efficient queries.
- TCMS-377 [Performance]Reporting Overall Section Optimize.
- TCMS-313 Support Read/Write separation solution in app level.
- TCMS-344 [XMLRPC] Log all XMLRPC invocations in database log table.

* Fri Jun 27 2014 Jian Chen <jianchen@redhat.com> 3.8.8-2
- Package for release to production.

* Thu Jun 05 2014 Jian Chen <jianchen@redhat.com> 3.8.8-1
- TCMS-217 [feature]Provide function that can add bug ID(JIRA) to test case run
- TCMS-286 Distribute document in standalone RPM package
- TCMS-297 [Slow Query] fix sql query that queries test cases
- TCMS-309 Use iterator when loop queryset in xmlrpc
- TCMS-232 [Performance] speed up loading /run/${run_id}/assigncase and update
- TCMS-174 Improve XMLRPC *.update()
- TCMS-224 [XMLRPC] Display more XMLRPC log information in admin page
- TCMS-222 Non-block mail notification
- TCMS-290 [Performance] XMLRPC method Product.get_cases cause Web Server occupies nearly 100% CPU time
- TCMS-323 Provide Product.{add,update,remove}_component() methods

* Mon May 26 2014 Chenxiong Qi <cqi@redhat.com> 3.8.7-6
- Package for release to production

* Thu May 22 2014 Chenxiong Qi <cqi@redhat.com> - 3.8.7-5
- TCMS-326 - [XMLRPC] Optimize TestRun.get_test_cases, which generates a slow query that would affect other SQL execution on test_case_runs table

* Tue Apr 22 2014 Jian Chen <jianchen@redhat.com> - 3.8.7-3
- TCMS-264 - Temp workaround to avoid updates automatically bugzilla with TCMS test case ID.
- TCMS-240 - Convert column type, add composite index and add migrate sql for each release version.

* Fri Apr 11 2014 Jian Chen <jianchen@redhat.com> - 3.8.7-2
- Bug 1083958 - [test run]In run detail page, using 'bugs-remove' link can remove the bug which does not belong to the current caserun.
- Bug 1083965 - [test run]In run detail page, using 'comment-add' link to add comment, system does not record author.

* Thu Apr 03 2014 Chenxiong Qi <cqi@redhat.com> - 3.8.7-1
- Bug 1034100 - [Performance] opening plan/id/chooseruns page causes Python interpreter consumes very hight, around 100%, CPU usage
- TCMS-171 [BZ 866974] Provide TestPlan.{add,get,remove}_component
- TCMS-177 It takes over one min to mark one case to pass in test case run.
- TCMS-186 Too slow when create test run
- TCMS-187 [Performance] Loading test case when expand a test case pane in Cases and Reviewing Cases tabs in a test plan page is too slow.
- TCMS-188 [Performance] Loading test case when expand a test case pane in test run page is too slow
- TCMS-194 [Performance] Expand a plan to display case run list in Case Runs tab in a case page
- TCMS-195 [Performance] Expand a case run from case run list in Case Runs tab in a case page
- Using VERSION.txt file instead of writing version into tcms module directly

* Tue Apr 01 2014 Chenxiong Qi <cqi@redhat.com> - 3.8.6-5
- 1082150 Backward-incompatible change in TestRun.get_test_case_runs()

* Tue Dec 10 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-5
- 1036538 [advance search]printable copy, test cases is null even if select cases/plan from advance search list
- 1036678 [Print plan]No cases information in print view page

* Wed Dec 4 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-4
- 1036028 [Test plan] Unable to calculate all run progress even if I select "Also select the rest XX page(s)"
- 1036598 [Add tag]"6932 undefined" warning when add tag without select "Also select cases that are not shown below, yet."
- 1036538 [advance search]printable copy, test cases is null even if select cases/plan from advance search list
- 1036672 [export all cases]Export all cases result is blank
- 1036678 [Print plan]No cases infomation in print view page
- 1036609 [Test Plan]Unable to set default tester in test plan
- 1036627 [Test Plan]Unable to batch set status in test plan
- 1036629 [Test Plan]Unable to batch set priority in test plan
- 1036508 [advance search]Can not export selected test cases/plan to download file from advance search list
- 1036042 [RFE]Suggest change the description of "Also select cases that are not shown below, yet." in test plan
- 1035956 [test plan]Unable to create new test run or add cases to existing run

* Thu Nov 28 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-3
- Bug 1028863 - [Testplan][Runs] In 'Runs' label of a Test plan, not input any thing in 'Items Per Page' then search, the site have no responce
- Bug 1028921 - [TestPlan][Cases] It is better if the select all function can select all the cases which are filtered
- Bug 1032897 - Test runs of a Test plan a displayed incorrectly
- Bug 1032969 - Missing progress bar on test run search result

* Wed Nov 13 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-2
- Using a separated file to track all database changes

* Tue Nov 12 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-1
- Bug 1017112 - [Performance] Loading TestRuns in pagination way in the TestPlan page
- Bug 1018021 - [Performance] Search TestPlan without any criteria causes MySQL occurpies nearly 100% CPU time
- Bug 1019641 - Lazy-loading TreeView tab in a TestPlan page
- Bug 1017110 - [Performace] Loading Reviewing TestCases in pagination way in the TestPlan page
- Bug 1017102 - [Performace] Loading TestCases in pagination way in the TestPlan page
- Bug 1017255 - [Performance] Rewrite implementation of TestCase' progressbar
- Bug 1024289 - [Advanced Search] Components/Versions/Categories/Builds are not shown after select a Product in 'Advanced Search' page
- Bug 1025657 - [Cases] Python error page is shown if input full-width characters in 'Default Tester' when add/edit a case
- Bug 1024680 - [Home][Basic Information] The Python error page is shown if Name is invalid in Basic Information

* Tue Sep 17 2013 Jian Chen <jianchen@redhat.com> - 3.8.4
- Add a column with number of comments into Case Runs table
- Several Bug Fixes (Refer to ChangeLog)

* Thu Jul 25 2013 Chaobin Tang <ctang@redhat.com> - 3.8.2
- XMLRPC API (Refer to ChangeLog)

*Mon Jul 11 2011 Chaobin Tang <ctang@redhat.com> - 3.5
- Usability Improvements (Refer to ChangeLog)

*Thu Mar 3 2011 Chaobin Tang <ctang@redhat.com> - 3.4.1
- Testing Report Implementation
- Several Bug Fixes (Refer to ChangeLog)

*Thu Mar 3 2011 Chaobin Tang <ctang@redhat.com> - 3.4
- Advance Search Implementation
- Several Bug Fixes (Refer to ChangeLog)

*Fri Feb 25 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-3
- Upstream released new version

*Tue Feb 15 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-2
- Upstream released new version

*Mon Jan 24 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-1
- Upstream released new version
- Include apache QPID support
- Completed global signal processor

* Wed Dec 1 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-4
- Upstream released new version

* Tue Nov 30 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-3
- Upstream released new version

* Tue Nov 23 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-2
- Upstream released new version

* Tue Nov 9 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-1
- Upstream released new version

* Fri Sep 17 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-3
- Upstream released new version

* Wed Sep 15 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-2
- Upstream released new version

* Wed Sep 8 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-1
- Upstream released new version
- Add highcharts for future reporting
- Add django-pagination support.

* Thu Aug 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.0-2
- Upstream released new version

* Thu Aug 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.0-1
- Upstream released new version

* Mon Aug 2 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-3
- Upstream released new version

* Fri Jul 30 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-2
- Upstream released new version

* Wed Jul 21 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-1
- Upstream released new version

* Mon Jun 28 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-2.svn2859
- Upstream released new version

* Sat Jun 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-1.svn2841
- Upstream released new version

* Tue Jun 8 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-2.svn2819
- Upstream released new version

* Thu Jun 3 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-1.svn2805
- Upstream released new version
- Add JavaScript library 'livepiple'.

* Wed May 19 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-3.svn2748
- Upstream released new version

* Thu May 13 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-2.svn2736
- Upstream released new version

* Tue May 11 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-1.svn2728
- Upstream released new version

* Fri Apr 16 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b2.svn2665
- Upstream released new version

* Wed Apr 14 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b1.svn2650
- Upstream released new version

* Thu Apr 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-5.svn2599
- Upstream released new version

* Mon Mar 29 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-4.svn2594
- Upstream released new version

* Tue Mar 23 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-3.svn2577
- Upstream released new version

* Mon Mar 22 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-2.svn2568
- Upstream released new version

* Thu Mar 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-1.svn2564
- Upstream released new version

* Wed Mar 17 2010 Xuqing Kuang <xkuang@redhat.com> -2.2-4.svn2504
- Upstream released new version

* Fri Mar 12 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-3.svn2504
- Upstream released new version

* Thu Mar 4 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-2.svn2504
- Upstream released new version

* Mon Mar 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-1.svn2500
- Upstream released new version

* Thu Feb 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-4.svn2461
- Upstream released new version

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-3.svn2449
- Upstream released new version

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-2.svn2446
- Upstream released new version

* Mon Feb 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-1.svn2443
- Upstream released new version

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn2403
- Upstream released new version

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn2402
- Upstream released new version

* Fri Jan 15 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn2394
- Upstream released new version

* Mon Jan 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1RC.svn2368
- Upstream released new version

* Tue Dec 29 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1beta.svn2318
- Upstream released new version

* Fri Dec 18 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-3.svn2261
- Upstream released new version

* Tue Dec 8 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-2.svn2229
- Upstream released new version

* Fri Dec 4 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-1.svn2213
- Upstream released new version

* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-3.svn2167
- Upstream released new version

* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-2.svn2167
- Upstream released new version

* Fri Nov 20 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-1.svn2143
- Upstream released new version

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.1-1.svn2097
- Upstream released new version

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-9.svn2046
- Upstream released new version

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-7.svn2046.RC
- Upstream released new version

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-6.svn2046.RC
- Upstream released new version

* Wed Oct 21 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-5.svn2042.RC
- Upstream released new version

* Fri Oct 16 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-4.svn2006.RC
- Upstream released new version

* Wed Oct 14 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn1971
- Upstream released new version

* Wed Sep 30 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1938
- Upstream released new version

* Wed Sep 23 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1898
- Upstream released new version

* Tue Sep 15 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1863
- Upstream released new version

* Tue Sep 1 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1833
- Upstream released new version

* Wed Jul 22 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1799
- Upstream released new version

* Thu Mar 19 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-6.svn1547
- Upstream released new version

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-5.svn1935
- Upstream released new version

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-4.svn1935
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-3.svn1487
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-2.svn1487
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-1.svn1487
- Upstream released new version

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-4
- Upstream released new version

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-3
- Upstream released new version

* Wed Feb 18 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-2.svn1309
- Upstream released new version
- add mod_python and python-memcached dependencies
- add apache config to correct location

* Thu Feb 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-1.svn1294
- initial packaging
