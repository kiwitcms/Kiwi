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

    class Meta:
        db_table = u'products'

    def __str__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import ProductXMLRPCSerializer
        _query = query or {}
        qs = cls.objects.filter(**_query).order_by('pk')
        serializer = ProductXMLRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

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
        query = self.build
        if only_active:
            query = self.build.filter(is_active=True)
        return get_as_choices(query.all(), allow_blank)

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
        serializer = BuildXMLRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

    @classmethod
    def list_active(cls, query={}):
        if isinstance(query, dict):
            query['is_active'] = True
        return cls.objects.filter(**query)

    def __str__(self):
        return self.name

    def as_choice(self):
        return (self.build_id, self.name)

    def get_case_runs_failed_percent(self):
        if hasattr(self, 'case_runs_failed_count'):
            return calc_percent(self.case_runs_failed_count,
                                self.case_runs_count)
        return None

    def get_case_runs_passed_percent(self):
        if hasattr(self, 'case_runs_passed_count'):
            return calc_percent(self.case_runs_passed_count,
                                self.case_runs_count)
        return None


# Test tag zone
class Tag(TCMSActionModel):
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


class EnvGroup(TCMSActionModel):
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
        'management.EnvProperty',
        through='management.EnvGroupPropertyMap',
        related_name='group'
    )

    class Meta:
        db_table = u'tcms_env_groups'

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class EnvProperty(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = u'tcms_env_properties'

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class EnvGroupPropertyMap(models.Model):
    group = models.ForeignKey(EnvGroup, on_delete=models.CASCADE)
    property = models.ForeignKey(EnvProperty, on_delete=models.CASCADE)

    class Meta:
        db_table = u'tcms_env_group_property_map'


class EnvValue(TCMSActionModel):
    value = models.CharField(max_length=255)
    property = models.ForeignKey(EnvProperty, related_name='value', on_delete=models.CASCADE)
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
