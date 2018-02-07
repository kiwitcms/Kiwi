# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.db import models
from django.conf import settings

from tcms.core.models import TCMSActionModel
from tcms.core.utils import calc_percent

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

    def __str__(self):
        return self.name


class Product(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    milestone_url = models.CharField(db_column='milestoneurl', max_length=128, default='---')
    disallow_new = models.BooleanField(db_column='disallownew', default=False)
    vote_super_user = models.IntegerField(db_column='votesperuser', null=True, default=True)
    max_vote_super_bug = models.IntegerField(db_column='maxvotesperbug', default=10000)
    votes_to_confirm = models.BooleanField(db_column='votestoconfirm', default=False)
    default_milestone = models.CharField(db_column='defaultmilestone',
                                         max_length=20, default='---')

    class Meta:
        db_table = u'products'

    def __str__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import ProductXMLRPCSerializer
        _query = query or {}
        qs = cls.objects.filter(**_query).order_by('pk')
        s = ProductXMLRPCSerializer(model_class=cls, queryset=qs)
        return s.serialize_queryset()

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)
        # reverse many-to-one relations from other models
        # which point to Product via FK
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

    def __str__(self):
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    value = models.CharField(unique=True, max_length=60)
    sortkey = models.IntegerField(default=0)

    class Meta:
        db_table = u'milestones'

    def __str__(self):
        return self.value


class Component(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(max_length=64)
    product = models.ForeignKey(Product, related_name='component', on_delete=models.CASCADE)
    initial_owner = models.ForeignKey(
        'auth.User',
        db_column='initialowner',
        related_name='initialowner',
        null=True,
        on_delete=models.CASCADE
    )
    initial_qa_contact = models.ForeignKey(
        'auth.User',
        db_column='initialqacontact',
        related_name='initialqacontact',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    description = models.TextField()

    # Auto-generated attributes from back-references:
    #   'cases' : list of TestCases (from TestCases.components)

    class Meta:
        db_table = u'components'
        unique_together = ('product', 'name')

    def __str__(self):
        return self.name


class Version(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=192)
    product = models.ForeignKey(Product, related_name='version', on_delete=models.CASCADE)

    class Meta:
        db_table = u'versions'
        unique_together = ('product', 'value')

    def __str__(self):
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


class Build(TCMSActionModel):
    build_id = models.AutoField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, related_name='build', on_delete=models.CASCADE)
    milestone = models.CharField(max_length=20, default='---')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
        db_table = u'test_builds'
        unique_together = ('product', 'name')
        verbose_name = u'build'
        verbose_name_plural = u'builds'

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import BuildXMLRPCSerializer
        _query = query or {}
        qs = cls.objects.filter(**_query).order_by('pk')
        s = BuildXMLRPCSerializer(model_class=cls, queryset=qs)
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

    def __str__(self):
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


# Test tag zone
class TestTag(TCMSActionModel):
    id = models.AutoField(db_column='tag_id', max_length=10, primary_key=True)
    name = models.CharField(db_column='tag_name', max_length=255)

    class Meta:
        db_table = u'test_tags'
        verbose_name = u'tag'
        verbose_name_plural = u'tags'

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create_many_by_name(cls, names):
        tags = []
        for name in names:
            new_tag = cls.objects.get_or_create(name=name)[0]
            tags.append(new_tag)
        return tags


class TCMSEnvGroup(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='env_group_manager',
                                on_delete=models.CASCADE)
    modified_by = models.ForeignKey(
        'auth.User',
        related_name='env_group_modifier',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    property = models.ManyToManyField(
        'management.TCMSEnvProperty',
        through='management.TCMSEnvGroupPropertyMap',
        related_name='group'
    )

    class Meta:
        db_table = u'tcms_env_groups'

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class TCMSEnvProperty(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = u'tcms_env_properties'

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class TCMSEnvGroupPropertyMap(models.Model):
    group = models.ForeignKey(TCMSEnvGroup, on_delete=models.CASCADE)
    property = models.ForeignKey(TCMSEnvProperty, on_delete=models.CASCADE)

    class Meta:
        db_table = u'tcms_env_group_property_map'


class TCMSEnvValue(TCMSActionModel):
    value = models.CharField(max_length=255)
    property = models.ForeignKey(TCMSEnvProperty, related_name='value', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = u'tcms_env_values'
        unique_together = ('property', 'value')
        ordering = ['property__name', 'value']

    def __str__(self):
        return self.value

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)
