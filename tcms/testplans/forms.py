# -*- coding: utf-8 -*-
from django import forms

from odf.odf2xhtml import ODF2XHTML, load
from tinymce.widgets import TinyMCE

from tcms.core.utils import string_to_list
from tcms.core.forms.fields import UserField, StripURLField
from tcms.management.models import Product, Version, EnvGroup, Tag
from .models import TestPlan, PlanType
# ===========Plan Fields==============


MIMETYPE_HTML = 'text/html'
MIMETYPE_PLAIN = 'text/plain'
MIMETYPE_OCTET_STREAM = 'application/octet-stream'
MIMETYPE_OPENDOCUMENT = 'application/vnd.oasis.opendocument.text'


class UploadedFile(object):  # pylint: disable=too-few-public-methods
    """Base class for all classes representing a concrete uploaded file"""

    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file

    def get_content(self):
        raise NotImplementedError('Must be implemented in subclass.')


class UploadedPlainTextFile(UploadedFile):  # pylint: disable=too-few-public-methods
    """Represent an uploaded plain text file"""

    def get_content(self):
        return '<pre>{0}</pre>'.format(self.uploaded_file.read())


class UploadedHTMLFile(UploadedFile):  # pylint: disable=too-few-public-methods
    """Represent an uploaded HTML file

    While uploading an HTML file, several tags, attributee have to be deleted,
    because they would break Kiwi TCMS's internal JavaScript features and styles
    and make some features unusable. Especially to the JavaScript surrounded by
    SCRIPT or referenced from unknown external resources, security issue must
    be considered.

    Currently, tags SCRIPT, STYLE AND LINK are removed. And attributes class,
    style and id are removed.
    """

    def get_content(self):
        def remove_tag(tag):
            return tag.extract()

        from bs4 import BeautifulSoup
        from itertools import chain

        soup = BeautifulSoup(self.uploaded_file.read(), 'html.parser')
        find_all = soup.body.find_all

        map(remove_tag, chain(find_all('script'),
                              find_all('style'),
                              find_all('link')))

        for tag in soup.body.find_all():
            pop = tag.attrs.pop
            pop('class', None)
            pop('CLASS', None)
            pop('style', None)
            pop('STYLE', None)
            pop('id', None)
            pop('ID', None)

        return soup.body


class UploadedODTFile(UploadedFile):  # pylint: disable=too-few-public-methods
    """Represent an uploaded ODT file"""

    def get_content(self):
        generatecss = True
        embedable = True
        odhandler = ODF2XHTML(generatecss, embedable)

        doc = load(self.uploaded_file)
        return odhandler.odf2xhtml(doc)


class PlanFileField(forms.FileField):
    ODT_CONTENT_TYPES = (MIMETYPE_OCTET_STREAM, MIMETYPE_OPENDOCUMENT)

    default_error_messages = {
        'invalid_file_type': 'The file you uploaded is not a correct, '
                             'Html/Plain text/ODT file.',
        'unexcept_odf_error': 'Unable to analyse the file or the file you '
                              'upload is not Open Document.',
        'unexpected_html_error': 'Invalid HTML document.',
    }

    def clean(self, data, initial=None):
        plan_file_field = super(PlanFileField, self).clean(data, initial)

        if plan_file_field is None:
            return None

        if not data and initial:
            return initial

        if data.content_type in self.ODT_CONTENT_TYPES:
            try:
                return UploadedODTFile(data).get_content()
            except Exception:
                raise forms.ValidationError(
                    self.error_messages['unexcept_odf_error'])

        if data.content_type == MIMETYPE_HTML:
            try:
                return UploadedHTMLFile(data).get_content()
            except Exception:
                raise forms.ValidationError(
                    self.error_messages['unexpected_html_error'])

        if data.content_type == MIMETYPE_PLAIN:
            return UploadedPlainTextFile(data).get_content()

        raise forms.ValidationError(self.error_messages['invalid_file_type'])


# =========== New Plan ModelForm ==============


class PlanModelForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        exclude = ('author', )


# =========== Forms for create/update ==============


class BasePlanForm(forms.Form):
    name = forms.CharField(label="Plan name")
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        empty_label=None,
    )
    text = forms.CharField(
        label="Plan Document",
        widget=TinyMCE(),
        required=False
    )
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        empty_label=None,
    )
    product_version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        empty_label=None,
    )
    extra_link = StripURLField(
        label='Extra link',
        max_length=1024,
        required=False
    )
    env_group = forms.ModelChoiceField(
        label="Environment Group",
        queryset=EnvGroup.get_active().all(),
        required=False
    )
    parent = forms.IntegerField(required=False)

    owner = forms.CharField(
        label="Plan Document",
        required=False
    )

    def clean_parent(self):
        try:
            parent_pk = self.cleaned_data['parent']
            if parent_pk:
                return TestPlan.objects.get(pk=parent_pk)
        except TestPlan.DoesNotExist:
            raise forms.ValidationError('The plan does not exist in database.')

    def populate(self, product_id):
        if product_id:
            self.fields['product_version'].queryset = Version.objects.filter(
                product__id=product_id)
        else:
            self.fields['product_version'].queryset = Version.objects.all()


class NewPlanForm(BasePlanForm):
    upload_plan_text = PlanFileField(required=False)
    tag = forms.CharField(
        label="Tag",
        required=False
    )

    # Display radio buttons instead of checkboxes
    auto_to_plan_owner = forms.BooleanField(
        label=' plan\'s owner',
        required=False
    )
    auto_to_plan_author = forms.BooleanField(
        label=' plan\'s author',
        required=False
    )
    auto_to_case_owner = forms.BooleanField(
        label=' the author of the case under a plan',
        required=False
    )
    auto_to_case_default_tester = forms.BooleanField(
        label=' the default tester of the case under a plan',
        required=False
    )
    notify_on_plan_update = forms.BooleanField(
        label=' when plan is updated',
        required=False
    )
    notify_on_case_update = forms.BooleanField(
        label=' when cases of a plan are updated',
        required=False
    )

    def clean_tag(self):
        return Tag.objects.filter(
            name__in=string_to_list(self.cleaned_data['tag'])
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get('upload_plan_text'):
            cleaned_data['text'] = cleaned_data['upload_plan_text']
        return cleaned_data


class EditPlanForm(NewPlanForm):
    product_version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.all(),
        empty_label=None,
    )
    is_active = forms.BooleanField(label="Active", required=False)
    owner = UserField(
        label=' plan\'s owner',
        required=False
    )
    author = UserField(
        label=' plan\'s author',
        required=False
    )


# =========== Forms for search/filter ==============

class SearchPlanForm(forms.Form):
    pk = forms.IntegerField(required=False)
    pk__in = forms.CharField(required=False)
    parent__pk = forms.IntegerField(required=False)
    search = forms.CharField(label="Search", required=False)
    plan_id = forms.IntegerField(label="Plan ID", required=False)
    name__icontains = forms.CharField(label="Plan name", required=False)
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        required=False
    )
    product_version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        required=False
    )
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False,
    )
    env_group = forms.ModelChoiceField(
        label="Environment Group",
        queryset=EnvGroup.get_active().all(),
        required=False
    )
    author__username__startswith = forms.CharField(required=False)
    author__email__startswith = forms.CharField(required=False)
    owner__username__startswith = forms.CharField(required=False)
    case__default_tester__username__startswith = forms.CharField(
        required=False)
    tag__name__in = forms.CharField(required=False)
    is_active = forms.BooleanField(required=False)
    create_date__gte = forms.DateTimeField(
        label='Create after', required=False,
        widget=forms.DateInput(attrs={
            'class': 'vDateField',
        })
    )
    create_date__lte = forms.DateTimeField(
        label='Create before', required=False,
        widget=forms.DateInput(attrs={
            'class': 'vDateField',
        })
    )

    def clean_pk__in(self):
        results = []
        try:
            for result in string_to_list(self.cleaned_data['pk__in']):
                results.append(int(result))
        except Exception as error:
            raise forms.ValidationError(str(error))

        return results

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data['tag__name__in'])

    def populate(self, product_id=None):
        if product_id:
            self.fields['product_version'].queryset = Version.objects.filter(
                product__id=product_id)
        else:
            self.fields['product_version'].queryset = Version.objects.all()


class ClonePlanForm(BasePlanForm):
    name = forms.CharField(label="Plan name", required=False)
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False,
    )
    keep_orignal_author = forms.BooleanField(
        label='Keep orignal author',
        help_text='Unchecking will make me the author of the copied plan',
        required=False,
    )
    copy_texts = forms.BooleanField(
        label='Copy Plan Document',
        required=False,
    )
    copy_environment_group = forms.BooleanField(
        label='Copy environment group',
        help_text='Check it on to copy environment group of the plan.',
        required=False
    )
    link_testcases = forms.BooleanField(
        label='All Test Cases',
        required=False
    )
    copy_testcases = forms.BooleanField(
        label='Create a copy',
        help_text='Unchecking will create a link to selected plans',
        required=False
    )
    maintain_case_orignal_author = forms.BooleanField(
        label='Maintain original authors',
        help_text='Unchecking will make me the author of the copied cases',
        required=False
    )
    keep_case_default_tester = forms.BooleanField(
        label='Keep Default Tester',
        help_text='Unchecking will make me the default tester of copied cases',
        required=False
    )
    set_parent = forms.BooleanField(
        label='Set source plan as parent',
        help_text='Check it to set the source plan as parent of new cloned '
                  'plan.',
        required=False
    )


# =========== Forms for XML-RPC functions ==============


class XMLRPCNewPlanForm(EditPlanForm):
    text = forms.CharField()


class XMLRPCEditPlanForm(EditPlanForm):
    name = forms.CharField(
        label="Plan name", required=False
    )
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False
    )
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        required=False,
    )
    product_version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        required=False
    )
