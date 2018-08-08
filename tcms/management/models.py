# -*- coding: utf-8 -*-

from django.db import models

from tcms.core.models import TCMSActionModel


class Classification(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    description = models.TextField(blank=True)
    sortkey = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Product(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    description = models.TextField(blank=True)

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


class Priority(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    value = models.CharField(unique=True, max_length=64)
    sortkey = models.IntegerField(default=0)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
        verbose_name_plural = u'priorities'

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
        unique_together = ('product', 'name')

    def __str__(self):
        return self.name


class Version(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=192)
    product = models.ForeignKey(Product, related_name='version', on_delete=models.CASCADE)

    class Meta:
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


class Build(TCMSActionModel):
    build_id = models.AutoField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, related_name='build', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
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


# Test tag zone
class Tag(TCMSActionModel):
    id = models.AutoField(db_column='tag_id', max_length=10, primary_key=True)
    name = models.CharField(db_column='tag_name', max_length=255)

    class Meta:
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
    is_active = models.BooleanField(default=True)
    property = models.ManyToManyField(
        'management.EnvProperty',
        through='management.EnvGroupPropertyMap',
        related_name='group'
    )

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class EnvProperty(TCMSActionModel):
    name = models.CharField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)


class EnvGroupPropertyMap(models.Model):
    group = models.ForeignKey(EnvGroup, on_delete=models.CASCADE)
    property = models.ForeignKey(EnvProperty, on_delete=models.CASCADE)


class EnvValue(TCMSActionModel):
    value = models.CharField(max_length=255)
    property = models.ForeignKey(EnvProperty, related_name='value', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('property', 'value')
        ordering = ['property__name', 'value']

    def __str__(self):
        return self.value

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True)
