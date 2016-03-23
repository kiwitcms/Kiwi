# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
        ('testplans', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='tcmsenvplanmap',
            name='plan',
            field=models.ForeignKey(to='testplans.TestPlan'),
        ),
        migrations.AddField(
            model_name='tcmsenvgrouppropertymap',
            name='group',
            field=models.ForeignKey(to='management.TCMSEnvGroup'),
        ),
        migrations.AddField(
            model_name='tcmsenvgrouppropertymap',
            name='property',
            field=models.ForeignKey(to='management.TCMSEnvProperty'),
        ),
        migrations.AddField(
            model_name='tcmsenvgroup',
            name='manager',
            field=models.ForeignKey(related_name='env_group_manager', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tcmsenvgroup',
            name='modified_by',
            field=models.ForeignKey(related_name='env_group_modifier', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='tcmsenvgroup',
            name='property',
            field=models.ManyToManyField(related_name='group', through='management.TCMSEnvGroupPropertyMap', to='management.TCMSEnvProperty'),
        ),
        migrations.AddField(
            model_name='product',
            name='classification',
            field=models.ForeignKey(to='management.Classification'),
        ),
        migrations.AddField(
            model_name='milestone',
            name='product',
            field=models.ForeignKey(to='management.Product'),
        ),
        migrations.AddField(
            model_name='component',
            name='initial_owner',
            field=models.ForeignKey(related_name='initialowner', db_column=b'initialowner', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='component',
            name='initial_qa_contact',
            field=models.ForeignKey(related_name='initialqacontact', db_column=b'initialqacontact', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='component',
            name='product',
            field=models.ForeignKey(related_name='component', to='management.Product'),
        ),
        migrations.AlterUniqueTogether(
            name='version',
            unique_together=set([('product', 'value')]),
        ),
        migrations.AlterIndexTogether(
            name='testenvironmentcategory',
            index_together=set([('product', 'name'), ('env_category_id', 'product')]),
        ),
        migrations.AlterUniqueTogether(
            name='testbuild',
            unique_together=set([('product', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='tcmsenvvalue',
            unique_together=set([('property', 'value')]),
        ),
        migrations.AlterUniqueTogether(
            name='component',
            unique_together=set([('product', 'name')]),
        ),
    ]
