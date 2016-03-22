# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.db import models

from tcms.core.models import BlobField
from tcms.core.models import TCMSActionModel
from tcms.core.utils import calc_percent

# FIXME: plugins_support is no longer available. dead code here.
try:
    from tcms.core.contrib.plugins_support.signals import register_model
except ImportError:
    register_model = None

# Products zone


def get_as_choices(iterable, allow_blank):
    # Generate a list of (id, string) pairs suitable
    # for a ChoiceField's "choices".
    #
    # Prepend with a blank entry if "allow_blank" is True
    #
    # Turn each object in the list into a choice
    # using its "as_choice" method
    if allow_blank:
        result = [('', '')]
    else:
        result = []
    result += [obj.as_choice() for obj in iterable]
    return result


def get_all_choices(cls, allow_blank=True):
    # Generate a list of (id, string) pairs suitable
    # for a ChoiceField's "choices", based on all instances of a class:
    return get_as_choices(cls.objects.all(), allow_blank)


class Classification(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    description = models.TextField(blank=True)
    sortkey = models.IntegerField(default=0)

    class Meta:
        db_table = u'classifications'

    def __unicode__(self):
        return self.name


class Product(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    classification = models.ForeignKey(Classification)
    description = models.TextField(blank=True)
    milestone_url = models.CharField(db_column='milestoneurl',
                                     max_length=128,
                                     default='---')
    disallow_new = models.BooleanField(db_column='disallownew', default=False)
    vote_super_user = models.IntegerField(db_column='votesperuser',
                                          null=True, default=True)
    max_vote_super_bug = models.IntegerField(db_column='maxvotesperbug',
                                             default=10000)
    votes_to_confirm = models.BooleanField(db_column='votestoconfirm', default=False)
    default_milestone = models.CharField(db_column='defaultmilestone',
                                         max_length=20,
                                         default='---')

    class Meta:
        db_table = u'products'

    def __unicode__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import ProductXMLRPCSerializer
        _query = query or {}
        qs = cls.objects.filter(**_query).order_by('pk')
        s = ProductXMLRPCSerializer(model_class=cls, queryset=qs)
        return s.serialize_queryset()

    def save(self):
        super(Product, self).save()
        self.category.get_or_create(name='--default--')
        self.version.get_or_create(value='unspecified')
        self.build.get_or_create(name='unspecified')

    def get_version_choices(self, allow_blank):
        # Generate a list of (id, string) pairs suitable
        # for a ChoiceField's "choices":
        return get_as_choices(self.version.all(), allow_blank)

    def get_build_choices(self, allow_blank, only_active):
        # Generate a list of (id, string) pairs suitable
        # for a ChoiceField's "choices"
        #
        # @only_active: restrict to only show builds flagged as "active"
        q = self.build
        if only_active:
            q = q.filter(is_active=True)
        return get_as_choices(q.all(), allow_blank)

    def get_environment_choices(self, allow_blank):
        # Generate a list of (id, string) pairs suitable
        # for a ChoiceField's "choices":
        return get_as_choices(self.environments.all(), allow_blank)

    @classmethod
    def get_choices(cls, allow_blank):
        # Generate a list of (id, string) pairs suitable
        # for a ChoiceField's "choices":
        print cls.objects.all()
        return get_as_choices(cls.objects.order_by('name').all(), allow_blank)

    def as_choice(self):
        return (self.id, self.name)


class Priority(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    value = models.CharField(unique=True, max_length=64)
    sortkey = models.IntegerField(default=0)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
        db_table = u'priority'
        verbose_name_plural = u'priorities'

    def __unicode__(self):
        return self.value

    cache_key_values = 'priority__value'

    @classmethod
    def get_values(cls):
        values = cache.get(cls.cache_key_values)
        if values is None:
            values = dict(cls.objects.values_list('pk', 'value').iterator())
            cache.set(cls.cache_key_values, values)
        return values

    def save(self, *args, **kwargs):
        result = super(Priority, self).save(*args, **kwargs)
        cache.delete(self.cache_key_values)
        return result


class Milestone(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product)
    value = models.CharField(unique=True, max_length=60)
    sortkey = models.IntegerField(default=0)

    class Meta:
        db_table = u'milestones'

    def __unicode__(self):
        return unicode(self.value)


class Component(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(max_length=64)
    product = models.ForeignKey(Product, related_name='component')
    initial_owner = models.ForeignKey(
        'auth.User',
        db_column='initialowner',
        related_name='initialowner',
        null=True
    )
    initial_qa_contact = models.ForeignKey(
        'auth.User',
        db_column='initialqacontact',
        related_name='initialqacontact',
        blank=True,
        null=True
    )
    description = models.TextField()

    # Auto-generated attributes from back-references:
    #   'cases' : list of TestCases (from TestCases.components)

    class Meta:
        db_table = u'components'
        unique_together = ('product', 'name')

    def __unicode__(self):
        return self.name


class Version(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=192)
    product = models.ForeignKey(Product, related_name='version')

    class Meta:
        db_table = u'versions'
        unique_together = ('product', 'value')

    def __unicode__(self):
        return self.value

    @classmethod
    def string_to_id(cls, product_id, value):
        try:
            return cls.objects.get(product__id=product_id,
                                   value=value).pk
        except cls.DoesNotExist:
            return None

    def as_choice(self):
        return (self.id, self.value)


#  Test builds zone
class TestBuildManager(models.Manager):

    pass
#    def get_plans_count(self):
#        return sum(self.values_list('plans_count', flat=True))


class TestBuild(TCMSActionModel):
    build_id = models.AutoField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, related_name='build')
    milestone = models.CharField(max_length=20, default='---')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(db_column='isactive', default=True)
    objects = TestBuildManager()

    class Meta:
        db_table = u'test_builds'
        unique_together = ('product', 'name')
        verbose_name = u'build'
        verbose_name_plural = u'builds'

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import TestBuildXMLRPCSerializer
        _query = query or {}
        qs = cls.objects.filter(**_query).order_by('pk')
        s = TestBuildXMLRPCSerializer(model_class=cls, queryset=qs)
        return s.serialize_queryset()

    @classmethod
    def list(cls, query):
        q = cls.objects

        if query.get('build_id'):
            q = q.filter(build_id=query['build_id'])
        if query.get('name'):
            q = q.filter(name=query['name'])
        if query.get('product'):
            q = q.filter(product=query['product'])
        if query.get('product_id'):
            q = q.filter(product__id=query['product_id'])
        if query.get('milestone'):
            q = q.filter(milestone=query['milestone'])
        if query.get('is_active'):
            q = q.filter(is_active=query['is_active'])

        return q.all()

    @classmethod
    def list_active(cls, query={}):
        if isinstance(query, dict):
            query['is_active'] = True
        return cls.list(query)

    def __unicode__(self):
        return self.name

    def as_choice(self):
        return (self.build_id, self.name)

    def get_case_runs_failed_percent(self):
        if hasattr(self, 'case_runs_failed_count'):
            return calc_percent(self.case_runs_failed_count,
                                self.case_runs_count)
        else:
            return None

    def get_case_runs_passed_percent(self):
        if hasattr(self, 'case_runs_passed_count'):
            return calc_percent(self.case_runs_passed_count,
                                self.case_runs_count)
        else:
            return None

# Test environments zone


class TestEnvironment(TCMSActionModel):
    environment_id = models.AutoField(
        max_length=10,
        primary_key=True
    )
    product = models.ForeignKey(Product, related_name='environments')
    name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(db_column="isactive", default=True)

    class Meta:
        db_table = u'test_environments'

    def __unicode__(self):
        return self.name

    def as_choice(self):
        return (self.environment_id, self.name)


class TestEnvironmentCategory(models.Model):
    env_category_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, related_name='environment_categories')
    name = models.CharField(unique=True, max_length=255, blank=True)

    class Meta:
        db_table = u'test_environment_category'
        index_together = (('env_category_id', 'product'), ('product', 'name'))

    def __unicode__(self):
        return self.name


class TestEnvironmentElement(models.Model):
    element_id = models.AutoField(max_length=10, primary_key=True)
    env_category = models.ForeignKey(TestEnvironmentCategory)
    name = models.CharField(unique=True, max_length=255, blank=True)
    parent = models.ForeignKey('self', null=True, related_name='parent_set')
    is_private = models.BooleanField(db_column='isprivate', default=False)

    class Meta:
        db_table = u'test_environment_element'

    def __unicode__(self):
        return self.name


class TestEnvironmentProperty(models.Model):
    property_id = models.IntegerField(primary_key=True)
    element = models.ForeignKey(TestEnvironmentElement)
    name = models.CharField(unique=True, max_length=255, blank=True)
    valid_express = models.TextField(db_column='validexp', blank=True)

    class Meta:
        db_table = u'test_environment_property'

    def __unicode__(self):
        return self.name


class TestEnvironmentMap(models.Model):
    environment = models.OneToOneField(TestEnvironment)
    property = models.ForeignKey(TestEnvironmentProperty)
    element = models.ForeignKey(TestEnvironmentElement)
    value_selected = models.TextField(blank=True)

    class Meta:
        db_table = u'test_environment_map'

    def __unicode__(self):
        return self.value_selected


# Test tag zone


class TestTag(TCMSActionModel):
    id = models.AutoField(db_column='tag_id', max_length=10, primary_key=True)
    name = models.CharField(db_column='tag_name', max_length=255)

    class Meta:
        db_table = u'test_tags'
        verbose_name = u'tag'
        verbose_name_plural = u'tags'

    def __unicode__(self):
        return self.name

    @classmethod
    def string_to_list(cls, string):
        from tcms.core.utils import string_to_list
        return string_to_list(string)

    @classmethod
    def get_or_create_many_by_name(cls, names):
        tags = []
        for name in names:
            new_tag = cls.objects.get_or_create(name=name)[0]
            tags.append(new_tag)
        return tags


# Test attachements file zone


class TestAttachment(models.Model):
    attachment_id = models.AutoField(max_length=10, primary_key=True)
    submitter = models.ForeignKey(
        'auth.User',
        related_name='attachments',
        blank=True,
        null=True
    )
    description = models.CharField(max_length=1024,
                                   blank=True,
                                   null=True)
    file_name = models.CharField(db_column='filename',
                                 max_length=255,
                                 unique=True, blank=True)
    stored_name = models.CharField(max_length=128,
                                   unique=True,
                                   blank=True, null=True)
    create_date = models.DateTimeField(db_column='creation_ts')
    mime_type = models.CharField(max_length=100)

    def __unicode__(self):
        return self.file_name

    class Meta:
        db_table = u'test_attachments'


class TestAttachmentData(models.Model):
    attachment = models.OneToOneField(TestAttachment)
    contents = BlobField(blank=True)

    class Meta:
        db_table = u'test_attachment_data'

# ============================
# New TCMS Environments models
# ============================


class TCMSEnvGroup(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    manager = models.ForeignKey('auth.User', related_name='env_group_manager')
    modified_by = models.ForeignKey(
        'auth.User',
        related_name='env_group_modifier',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    property = models.ManyToManyField(
        'management.TCMSEnvProperty',
        through='management.TCMSEnvGroupPropertyMap',
        related_name='group'
    )

    class Meta:
        db_table = u'tcms_env_groups'

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class TCMSEnvPlanMap(models.Model):
    plan = models.ForeignKey('testplans.TestPlan')
    group = models.ForeignKey(TCMSEnvGroup)

    class Meta:
        db_table = u'tcms_env_plan_map'


class TCMSEnvProperty(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = u'tcms_env_properties'

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class TCMSEnvGroupPropertyMap(models.Model):
    group = models.ForeignKey(TCMSEnvGroup)
    property = models.ForeignKey(TCMSEnvProperty)

    class Meta:
        db_table = u'tcms_env_group_property_map'


class TCMSEnvValue(TCMSActionModel):
    value = models.CharField(max_length=255)
    property = models.ForeignKey(TCMSEnvProperty, related_name='value')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = u'tcms_env_values'
        unique_together = ('property', 'value')

    def __unicode__(self):
        return unicode(self.value)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


# FIXME: plugins_support is no longer available, this is dead code.
if register_model:
    register_model(Classification)
    register_model(Product)
    register_model(Priority)
    register_model(Version)
    register_model(TestBuild)
    register_model(TestTag)
    register_model(Component)
    register_model(TCMSEnvGroup)
    register_model(TCMSEnvValue)
    register_model(TestAttachment)
