# -*- coding: utf-8 -*-
from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('testplans', '0001_initial'),
        ('management', '0001_initial'),
        ('testcases', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcasebug',
            name='case_run',
            field=models.ForeignKey(related_name='case_run_bug', default=None, blank=True, to='testruns.TestCaseRun', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcaseattachment',
            name='attachment',
            field=models.ForeignKey(to='management.TestAttachment', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcaseattachment',
            name='case',
            field=models.ForeignKey(related_name='case_attachment', default=None, to='testcases.TestCase', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcaseattachment',
            name='case_run',
            field=models.ForeignKey(related_name='case_run_attachment', default=None, to='testruns.TestCaseRun', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='attachment',
            field=models.ManyToManyField(related_name='cases', through='testcases.TestCaseAttachment', to='management.TestAttachment'),
        ),
        migrations.AddField(
            model_name='testcase',
            name='author',
            field=models.ForeignKey(related_name='cases_as_author', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='case_status',
            field=models.ForeignKey(to='testcases.TestCaseStatus', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='category',
            field=models.ForeignKey(related_name='category_case', to='testcases.TestCaseCategory', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='component',
            field=models.ManyToManyField(related_name='cases', through='testcases.TestCaseComponent', to='management.Component'),
        ),
        migrations.AddField(
            model_name='testcase',
            name='default_tester',
            field=models.ForeignKey(related_name='cases_as_default_tester', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='plan',
            field=models.ManyToManyField(related_name='case', through='testcases.TestCasePlan', to='testplans.TestPlan'),
        ),
        migrations.AddField(
            model_name='testcase',
            name='priority',
            field=models.ForeignKey(related_name='priority_case', to='management.Priority', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='reviewer',
            field=models.ForeignKey(related_name='cases_as_reviewer', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='testcase',
            name='tag',
            field=models.ManyToManyField(related_name='cases', through='testcases.TestCaseTag', to='management.TestTag'),
        ),
        migrations.AddField(
            model_name='contact',
            name='content_type',
            field=models.ForeignKey(related_name='content_type_set_for_contact', verbose_name='content type', blank=True, to='contenttypes.ContentType', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='contact',
            name='site',
            field=models.ForeignKey(to='sites.Site', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='testcasetext',
            unique_together=set([('case', 'case_text_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='testcaseplan',
            unique_together=set([('plan', 'case')]),
        ),
        migrations.AlterUniqueTogether(
            name='testcasecategory',
            unique_together=set([('product', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='testcasebug',
            unique_together=set([('bug_id', 'case_run', 'case'), ('bug_id', 'case_run')]),
        ),
        migrations.AlterIndexTogether(
            name='contact',
            index_together=set([('content_type', 'object_pk', 'site')]),
        ),
    ]
