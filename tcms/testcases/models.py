# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.translation import override
from django.db.models import ObjectDoesNotExist

import vinaigrette

from tcms.core.models import TCMSActionModel
from tcms.core.history import KiwiHistoricalRecords
from tcms.issuetracker.types import IssueTrackerType
from tcms.testcases.fields import MultipleEmailField


class TestCaseStatus(TCMSActionModel):
    id = models.AutoField(
        db_column='case_status_id', max_length=6, primary_key=True
    )
    # FIXME: if name has unique value for each status, give unique constraint
    # to this field. Otherwise, all SQL queries filtering upon this
    #        field will cost much time in the database side.
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Test case status"
        verbose_name_plural = "Test case statuses"

    def __str__(self):
        return self.name

    @classmethod
    def get_proposed(cls):
        return cls.objects.get(name='PROPOSED')

    @classmethod
    def get_confirmed(cls):
        return cls.objects.get(name='CONFIRMED')

    @classmethod
    def string_to_instance(cls, name):
        return cls.objects.get(name=name)

    def is_confirmed(self):
        with override('en'):
            return self.name == 'CONFIRMED'


# register model for DB translations
vinaigrette.register(TestCaseStatus, ['name'])


class Category(TCMSActionModel):
    id = models.AutoField(db_column='category_id', primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey('management.Product', related_name="category",
                                on_delete=models.CASCADE)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = u'test case categories'
        unique_together = ('product', 'name')

    def __str__(self):
        return self.name


class TestCase(TCMSActionModel):
    history = KiwiHistoricalRecords()

    case_id = models.AutoField(primary_key=True)
    create_date = models.DateTimeField(db_column='creation_date', auto_now_add=True)
    is_automated = models.BooleanField(default=False)
    script = models.TextField(blank=True, null=True)
    arguments = models.TextField(blank=True, null=True)
    extra_link = models.CharField(max_length=1024, default=None, blank=True, null=True)
    summary = models.CharField(max_length=255)
    requirement = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True)

    case_status = models.ForeignKey(TestCaseStatus, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='category_case',
                                 on_delete=models.CASCADE)
    priority = models.ForeignKey('management.Priority', related_name='priority_case',
                                 on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cases_as_author',
                               on_delete=models.CASCADE)
    default_tester = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       related_name='cases_as_default_tester',
                                       blank=True,
                                       null=True,
                                       on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 related_name='cases_as_reviewer',
                                 null=True,
                                 on_delete=models.CASCADE)

    # FIXME: related_name should be cases instead of case. But now keep it
    # named case due to historical reason.
    plan = models.ManyToManyField('testplans.TestPlan', related_name='case',
                                  through='testcases.TestCasePlan')

    component = models.ManyToManyField('management.Component', related_name='cases',
                                       through='testcases.TestCaseComponent')

    tag = models.ManyToManyField('management.Tag', related_name='case',
                                 through='testcases.TestCaseTag')

    def __str__(self):
        return self.summary

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import TestCaseXMLRPCSerializer
        from tcms.xmlrpc.utils import distinct_filter

        _query = query or {}
        qs = distinct_filter(TestCase, _query).order_by('pk')
        serializer = TestCaseXMLRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

    # todo: does this check permissions ???
    @classmethod
    def create(cls, author, values):
        """
        Create the case element based on models/forms.
        """
        case = cls.objects.create(
            author=author,
            is_automated=values['is_automated'],
            # sortkey = values['sortkey'],
            script=values['script'],
            arguments=values['arguments'],
            extra_link=values['extra_link'],
            summary=values['summary'],
            requirement=values['requirement'],
            case_status=values['case_status'],
            category=values['category'],
            priority=values['priority'],
            default_tester=values['default_tester'],
            notes=values['notes'],
            text=values['text'],
        )

        # todo: should use add_tag
        tags = values.get('tag')
        if tags:
            map(case.add_tag, tags)
        return case

    @classmethod
    def list(cls, query, plan=None):
        """List the cases with request"""
        from django.db.models import Q

        if not plan:
            queryset = cls.objects
        else:
            queryset = cls.objects.filter(plan=plan)

        if query.get('case_id_set'):
            queryset = queryset.filter(pk__in=query['case_id_set'])

        if query.get('search'):
            queryset = queryset.filter(
                Q(pk__icontains=query['search']) |
                Q(summary__icontains=query['search']) |
                Q(author__email__startswith=query['search'])
            )

        if query.get('summary'):
            queryset = queryset.filter(Q(summary__icontains=query['summary']))

        if query.get('author'):
            queryset = queryset.filter(
                Q(author__first_name__startswith=query['author']) |
                Q(author__last_name__startswith=query['author']) |
                Q(author__username__icontains=query['author']) |
                Q(author__email__startswith=query['author'])
            )

        if query.get('default_tester'):
            queryset = queryset.filter(
                Q(default_tester__first_name__startswith=query[
                    'default_tester']) |
                Q(default_tester__last_name__startswith=query[
                    'default_tester']) |
                Q(default_tester__username__icontains=query[
                    'default_tester']) |
                Q(default_tester__email__startswith=query[
                    'default_tester'])
            )

        if query.get('tag__name__in'):
            queryset = queryset.filter(tag__name__in=query['tag__name__in'])

        if query.get('category'):
            queryset = queryset.filter(category__name=query['category'].name)

        if query.get('priority'):
            queryset = queryset.filter(priority__in=query['priority'])

        if query.get('case_status'):
            queryset = queryset.filter(case_status__in=query['case_status'])

        # If plan exists, remove leading and trailing whitespace from it.
        plan_str = query.get('plan', '').strip()
        if plan_str:
            try:
                # Is it an integer?  If so treat as a plan_id:
                plan_id = int(plan_str)
                queryset = queryset.filter(plan__plan_id=plan_id)
            except ValueError:
                # Not an integer - treat plan_str as a plan name:
                queryset = queryset.filter(plan__name__icontains=plan_str)
        del plan_str

        if query.get('product'):
            queryset = queryset.filter(category__product=query['product'])

        if query.get('component'):
            queryset = queryset.filter(component=query['component'])

        if query.get('bug_id'):
            queryset = queryset.filter(case_bug__bug_id__in=query['bug_id'])

        if query.get('is_automated'):
            queryset = queryset.filter(is_automated=query['is_automated'])

        return queryset.distinct()

    def add_bug(self, bug_id, bug_system_id, summary=None, description=None,
                case_run=None, bz_external_track=False):
        bug, created = self.case_bug.get_or_create(
            bug_id=bug_id,
            case_run=case_run,
            bug_system_id=bug_system_id,
            summary=summary,
            description=description,
        )

        if created:
            if bz_external_track:
                bug_system = BugSystem.objects.get(pk=bug_system_id)
                issue_tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
                if not issue_tracker.is_adding_testcase_to_issue_disabled():
                    issue_tracker.add_testcase_to_issue([self], bug)
                else:
                    raise ValueError('Enable linking test cases by configuring API parameters '
                                     'for this Issue Tracker!')
        else:
            raise ValueError('Bug %s already exist.' % bug_id)

    def add_component(self, component):
        return TestCaseComponent.objects.get_or_create(case=self, component=component)

    def add_tag(self, tag):
        return TestCaseTag.objects.get_or_create(case=self, tag=tag)

    def get_bugs(self):
        return Bug.objects.select_related(
            'case_run', 'bug_system'
        ).filter(case__case_id=self.case_id)

    def get_previous_and_next(self, pk_list):
        current_idx = pk_list.index(self.pk)
        prev = TestCase.objects.get(pk=pk_list[current_idx - 1])
        try:
            _next = TestCase.objects.get(pk=pk_list[current_idx + 1])
        except IndexError:
            _next = TestCase.objects.get(pk=pk_list[0])

        return (prev, _next)

    def get_text_with_version(self, case_text_version=None):
        if case_text_version:
            try:
                return self.history.get(history_id=case_text_version).text
            except ObjectDoesNotExist:
                return self.text

        return self.text

    def remove_bug(self, bug_id, run_id=None):
        query = Bug.objects.filter(
            bug_id=bug_id,
            case=self.pk
        )
        if run_id:
            query = query.filter(case_run=run_id)
        else:
            query = query.filter(case_run__isnull=True)

        query.delete()

    def remove_component(self, component):
        # note: cannot use self.component.remove(component) on a ManyToManyField
        # which specifies an intermediary model so we use the model manager!
        self.component.through.objects.filter(case=self.pk, component=component.pk).delete()

    def remove_tag(self, tag):
        self.tag.through.objects.filter(case=self.pk, tag=tag.pk).delete()

    def _get_absolute_url(self, request=None):
        return reverse('testcases-get', args=[self.pk, ])

    def _get_email_conf(self):
        try:
            return self.email_settings
        except ObjectDoesNotExist:
            return TestCaseEmailSettings.objects.create(case=self)

    emailing = property(_get_email_conf)


class TestCasePlan(models.Model):
    plan = models.ForeignKey('testplans.TestPlan', on_delete=models.CASCADE)
    case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    sortkey = models.IntegerField(null=True, blank=True)

    # TODO: create FOREIGN KEY constraint on plan_id and case_id individually
    # in database.

    class Meta:
        unique_together = ('plan', 'case')


class TestCaseComponent(models.Model):
    case = models.ForeignKey(TestCase, on_delete=models.CASCADE)  # case_id
    component = models.ForeignKey('management.Component', on_delete=models.CASCADE)  # component_id


class TestCaseTag(models.Model):
    tag = models.ForeignKey('management.Tag', on_delete=models.CASCADE)
    case = models.ForeignKey(TestCase, on_delete=models.CASCADE)


class BugSystem(TCMSActionModel):
    """
        This model describes a bug tracking system used in
        Kiwi TCMS. Fields below can be configured via
        the admin interface and their meaning is:

        #. **name:** a visual name for this bug tracker, e.g. `Kiwi TCMS GitHub`;
        #. **description:** a longer description shown in the admin;
        #. **url_reg_exp:** shown as **URL format string** in the UI - a format string
           used to construct URLs from bug IDs;
        #. **validate_reg_exp:** regular expression used for bug ID validation;
        #. **tracker_type:** a select menu to specify what kind of external
           system we interface with, e.g. Bugzilla, JIRA, others;
           The available options for this field are automatically populated
           by Kiwi TCMS;

           .. warning::

                Once this field is set it can't be reset to ``NULL``. Although
                Kiwi TCMS takes care to handle misconfigurations we advise you to
                configure your API credentials properly!

        #. **base_url:** base URL of this bug tracker. This is used to construct
           other links to the issue tracker, e.g. link to view multiple bugs at once
           or when a user tries to report a bug directly from a TestCase. The browser will open
           another window with pre-defined values based on the test case being
           executed and the type of the external issue tracking system.

           .. warning::

                If this field is left empty funtionality that depends on it will be disabled!

        #. **api_url, api_username, api_password:** configuration for an internal RPC object
           that communicate to the issue tracking system when necessary. Depending on the
           actual type of IT we're interfacing with some of these values may not be necessary.
           Refer to :mod:`tcms.issuetracker.types` for more information!

           .. warning::

                This is saved as plain-text in the database because it needs to be passed
                to the internal RPC object!
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    url_reg_exp = models.CharField(
        max_length=8192,
        verbose_name='URL format string',
        help_text='A valid Python format string such as http://bugs.example.com/%s'
    )
    validate_reg_exp = models.CharField(
        max_length=128,
        verbose_name='RegExp for ID validation',
        help_text=r'A valid JavaScript regular expression such as ^\d$',
    )

    tracker_type = models.CharField(
        max_length=128,
        verbose_name='Type',
        help_text='This determines how Kiwi TCMS integrates with the IT system',
        default='IssueTrackerType',
    )

    base_url = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name='Base URL',
        help_text="""Base URL, for example <strong>https://bugzilla.example.com</strong>!
Leave empty to disable!
""")

    api_url = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name='API URL',
        help_text='This is the URL to which API requests will be sent. Leave empty to disable!')

    api_username = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name='API username')

    api_password = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name='API password or token')

    class Meta:
        verbose_name = 'Bug tracker'
        verbose_name_plural = 'Bug trackers'

    def __str__(self):
        return self.name

    @classmethod
    def get_by_id(cls, system_id):
        return cls.objects.get(pk=system_id)


class Bug(TCMSActionModel):
    bug_id = models.CharField(max_length=25)
    case_run = models.ForeignKey('testruns.TestExecution', default=None, blank=True, null=True,
                                 related_name='case_run_bug', on_delete=models.CASCADE)
    case = models.ForeignKey(TestCase, related_name='case_bug', on_delete=models.CASCADE)
    bug_system = models.ForeignKey(BugSystem, default=1, on_delete=models.CASCADE)
    summary = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (('bug_id', 'case_run', 'case'),
                           ('bug_id', 'case_run'))

    def unique_error_message(self, model_class, unique_check):
        """Specific to invalid bug id"""
        bug_id_uniques = (('bug_id', 'case_run', 'case'),
                          ('bug_id', 'case_run'))
        if unique_check in bug_id_uniques:
            return 'Bug %d exists in run %d already.' % (self.bug_id, self.case_run.pk)
        return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        return self.bug_id

    def get_name(self):
        if self.summary:
            return self.summary

        return self.bug_id

    def get_full_url(self):
        return self.bug_system.url_reg_exp % self.bug_id


class TestCaseEmailSettings(models.Model):
    case = models.OneToOneField(TestCase, related_name='email_settings', on_delete=models.CASCADE)
    notify_on_case_update = models.BooleanField(default=True)
    notify_on_case_delete = models.BooleanField(default=True)
    auto_to_case_author = models.BooleanField(default=True)
    auto_to_case_tester = models.BooleanField(default=True)
    auto_to_run_manager = models.BooleanField(default=True)
    auto_to_run_tester = models.BooleanField(default=True)
    auto_to_case_run_assignee = models.BooleanField(default=True)

    cc_list = models.TextField(default='')

    def add_cc(self, email_addrs):
        """Add email addresses to CC list

        Arguments:
        - email_addrs: str or list, holding one or more email addresses
        """

        emailaddr_list = self.get_cc_list()
        if not isinstance(email_addrs, list):
            email_addrs = [email_addrs]

        # skip addresses already in the list
        for address in email_addrs:
            if address not in emailaddr_list:
                emailaddr_list.append(address)

        self.cc_list = MultipleEmailField.delimiter.join(emailaddr_list)
        self.save()

    def get_cc_list(self):
        """ Return the whole CC list """
        if not self.cc_list:
            return []
        return self.cc_list.split(MultipleEmailField.delimiter)

    def remove_cc(self, email_addrs):
        """Remove one or more email addresses from EmailSettings' CC list

        If any email_addr is unknown, remove_cc will keep quiet.

        Arguments:
        - email_addrs: str or list, holding one or more email addresses
        """
        emailaddr_list = self.get_cc_list()
        if not isinstance(email_addrs, list):
            email_addrs = [email_addrs]
        for address in email_addrs:
            if address in emailaddr_list:
                emailaddr_list.remove(address)

        self.cc_list = MultipleEmailField.delimiter.join(emailaddr_list)
        self.save()
