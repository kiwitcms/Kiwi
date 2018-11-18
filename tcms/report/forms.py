# -*- coding: utf-8 -*-
from django import forms

from tcms.management.models import Component, Product, Build, Version
from tcms.testcases.models import Category


class CustomSearchForm(forms.Form):
    build = forms.ModelMultipleChoiceField(
        label='Build',
        queryset=Build.objects.none(),
        required=False,
    )
    product = forms.ModelChoiceField(
        label='Product',
        queryset=Product.objects.only('name').order_by('name'),
        empty_label=None,
        error_messages={
            'required': 'Product is required to generate this report.',
            'invalid_choice': '%(value)s is not a valid product ID for '
                              'generating this report.',
        })
    version = forms.ModelChoiceField(
        label='Product version',
        queryset=Version.objects.none(),
        required=False,
    )
    build_run__plan__name__icontains = forms.CharField(
        label='Plan name',
        required=False,
    )
    category = forms.ModelChoiceField(
        label='Case category',
        queryset=Category.objects.none(),
        required=False,
    )
    component = forms.ModelChoiceField(
        label='Case component',
        queryset=Component.objects.none(),
        required=False,
    )

    def populate(self, product_id):
        if product_id:
            self.fields['version'].queryset = Version.objects.filter(
                product__id=product_id).only('value')
            self.fields['build'].queryset = Build.objects.filter(
                product__id=product_id).only('name')
            self.fields['category'].queryset = \
                Category.objects.filter(product__id=product_id).only(
                    'name')
            self.fields['component'].queryset = \
                Component.objects.filter(product__id=product_id).only('name')


class CustomSearchDetailsForm(CustomSearchForm):
    build = forms.ModelChoiceField(
        label='Build',
        queryset=Build.objects.none(),
        error_messages={
            'required': 'A build is required to generate this report.',
            'invalid_choice': '%(value)s is not a valid test build ID for '
                              'generating this report.',
        })


REPORT_TYPES = (
    ('per_build_report', 'By Case-Run Tester'),
    ('per_priority_report', 'By Case Priority'),
    ('runs_with_rates_per_plan_tag', 'By Plan\'s Tag'),
    ('per_plan_tag_report', 'By Plan\'s Tag Per Tag View'),
    ('runs_with_rates_per_plan_build', 'By Plan & Build'),
    ('per_plan_build_report', 'By Plan & Build Per Plan View'),
)


class BasicTestingReportFormFields(forms.Form):
    """Testing report form with basic necessary fields"""

    product = forms.ModelChoiceField(
        required=True,
        label='Product',
        empty_label=None,
        queryset=Product.objects.only('name').order_by('name'),
        error_messages={
            'required': 'You have to select a product to generate this '
                        'testing report.',
            'invalid_choice': '%(value)s is not a valid product.',
        })

    build = forms.ModelMultipleChoiceField(
        required=False,
        label='Build',
        queryset=Build.objects.none(),
        error_messages={
            'invalid_pk_value': '%s is not a valid test build ID.',
            'invalid_choice': 'Test build ID %s does not exist.',
        })

    version = forms.ModelMultipleChoiceField(
        required=False,
        label='Version',
        queryset=Version.objects.none(),
        error_messages={
            'invalid_choice': 'Version ID %s does not exist.',
            'invalid_pk_value': '%s is not a valid version ID.',
        })

    created_since = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        error_messages={
            'invalid': 'The start execute date is invalid. The valid format'
                       ' is YYYY-MM-DD.',
        },
        widget=forms.TextInput(attrs={
            'id': 'created_since',
            'style': 'width:130px;',
            'class': 'vDateField',
        }))

    created_before = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        error_messages={
            'invalid': 'The end execute date is invalid. The valid format '
                       'is YYYY-MM-DD.',
        },
        widget=forms.TextInput(attrs={
            'id': 'created_before',
            'style': 'width:130px;',
            'class': 'vDateField',
        }))

    def populate(self, product_id):
        if product_id:
            self.fields['build'].queryset = Build.objects.filter(
                product=product_id).only('name')
            self.fields['version'].queryset = Version.objects.filter(
                product=product_id).only('value')
        else:
            self.fields['build'].queryset = Build.objects.none()
            self.fields['version'].queryset = Version.objects.none()


class TestingReportCaseRunsListForm(BasicTestingReportFormFields):
    """Form validation for viewing case runs from tesing report"""

    run = forms.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            'invalid': 'Run ID is not valid.',
            'min_value': '%(limit_value)s is not valid. Run ID should be an '
                         'integer that is greater than 0.',
        })

    priority = forms.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            'invalid': 'Priority ID is not valid.',
            'min_value': '%(limit_value)s is not valid. Priority ID should '
                         'be an integer that is greater than 0.',
        })

    tester = forms.IntegerField(
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'User ID is not valid.',
            'min_value': '%(limit_value)s is not valid. User ID should be an'
                         ' integer that is greater than and equal to 0',
        })

    # Whatever the status name is passed from client, it doesn't matter. When
    # pass an invalid status name, no data will be queried.
    status = forms.CharField(
        required=False,
        max_length=30,
        error_messages={
            'max_length': 'Are you sure this is the status name you want?',
        })

    plan_tag = forms.CharField(
        required=False,
        max_length=30,
        error_messages={
            'max_length': 'Are your sure this is the tag you want?',
        })


class TestingReportForm(BasicTestingReportFormFields):
    """Criteria for generating testing report"""

    report_type = forms.ChoiceField(
        required=True,
        choices=REPORT_TYPES,
        initial='per_build_report',
        error_messages={
            'invalid_choice': '%(value)s is not a valid report type.',
        },
        widget=forms.RadioSelect)
