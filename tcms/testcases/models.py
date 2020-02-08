# -*- coding: utf-8 -*-
import vinaigrette
from django.conf import settings
from django.db import models
from django.db.models import ObjectDoesNotExist
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import override

from tcms.core.history import KiwiHistoricalRecords
from tcms.core.models import TCMSActionModel
from tcms.rpc.serializer import TestCaseRPCSerializer
from tcms.rpc.utils import distinct_filter
from tcms.testcases.fields import MultipleEmailField


# todo: this entire model should be removed and replaced with a boolean flag,
# e.g. TestCase.is_confirmed where False indicates that TC is not ready for
# execution yet - could be under peer review, could be new (unreviewed) or other
class TestCaseStatus(TCMSActionModel):
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

    def is_confirmed(self):
        with override('en'):
            return self.name == 'CONFIRMED'


# register model for DB translations
vinaigrette.register(TestCaseStatus, ['name'])


class Category(TCMSActionModel):
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

    create_date = models.DateTimeField(auto_now_add=True)
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

        _query = query or {}
        qs = distinct_filter(TestCase, _query).order_by('pk')
        serializer = TestCaseRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

    @classmethod
    def list(cls, query, plan=None):
        """List the cases with request"""

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
        # todo: this is the same as the if condition above !!! - this entire method
        # should be removed in favor of API
        plan_str = query.get('plan', '').strip()
        if plan_str:
            try:
                # Is it an integer?  If so treat as a plan_id:
                plan_id = int(plan_str)
                queryset = queryset.filter(plan__pk=plan_id)
            except ValueError:
                # Not an integer - treat plan_str as a plan name:
                queryset = queryset.filter(plan__name__icontains=plan_str)
        del plan_str

        if query.get('product'):
            queryset = queryset.filter(category__product=query['product'])

        if query.get('component'):
            queryset = queryset.filter(component=query['component'])

        if query.get('is_automated'):
            queryset = queryset.filter(is_automated=query['is_automated'])

        return queryset.distinct()

    def add_component(self, component):
        return TestCaseComponent.objects.get_or_create(case=self, component=component)

    def add_tag(self, tag):
        return TestCaseTag.objects.get_or_create(case=self, tag=tag)

    def get_text_with_version(self, case_text_version=None):
        if case_text_version:
            try:
                return self.history.get(history_id=case_text_version).text
            except ObjectDoesNotExist:
                return self.text

        return self.text

    def remove_component(self, component):
        # note: cannot use self.component.remove(component) on a ManyToManyField
        # which specifies an intermediary model so we use the model manager!
        self.component.through.objects.filter(case=self.pk, component=component.pk).delete()

    def remove_tag(self, tag):
        self.tag.through.objects.filter(case=self.pk, tag=tag.pk).delete()

    def _get_absolute_url(self, request=None):
        return reverse('testcases-get', args=[self.pk, ])

    def get_absolute_url(self):
        return self._get_absolute_url()

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

    class Meta:
        unique_together = ('plan', 'case')


class TestCaseComponent(models.Model):
    case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    component = models.ForeignKey('management.Component', on_delete=models.CASCADE)


class TestCaseTag(models.Model):
    tag = models.ForeignKey('management.Tag', on_delete=models.CASCADE)
    case = models.ForeignKey(TestCase, on_delete=models.CASCADE)


class BugSystem(TCMSActionModel):
    """
        This model describes a bug tracking system used in
        Kiwi TCMS. Fields below can be configured via
        the admin interface and their meaning is:

        #. **name:** a visual name for this bug tracker, e.g. `Kiwi TCMS GitHub`;
        #. **tracker_type:** a select menu to specify what kind of external
           system we interface with, e.g. Bugzilla, JIRA, others;
           The available options for this field are automatically populated
           by Kiwi TCMS;

           .. warning::

                Once this field is set it can't be reset to ``NULL``. Although
                Kiwi TCMS takes care to handle misconfigurations we advise you to
                configure your API credentials properly!

        #. **base_url:** base URL of this bug tracker.

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
