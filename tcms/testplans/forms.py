# -*- coding: utf-8 -*-
from django import forms

from odf.odf2xhtml import ODF2XHTML, load

from tcms.core.forms.fields import UserField, StripURLField
from tinymce.widgets import TinyMCE
from tcms.management.models import Component, Product, Version, TCMSEnvGroup, TestTag
from models import TestPlan, TestPlanType
from tcms.utils.xml import clean_xml_file, process_case
# ===========Plan Fields==============


MIMETYPE_HTML = 'text/html'
MIMETYPE_PLAIN = 'text/plain'
MIMETYPE_OCTET_STREAM = 'application/octet-stream'
MIMETYPE_OPENDOCUMENT = 'application/vnd.oasis.opendocument.text'


class UploadedFile(object):
    '''Base class for all classes representing a concrete uploaded file'''

    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file

    def get_content(self):
        raise NotImplementedError('Must be implemented in subclass.')


class UploadedPlainTextFile(UploadedFile):
    '''Represent an uploaded plain text file'''

    def get_content(self):
        return '<pre>{0}</pre>'.format(self.uploaded_file.read())


class UploadedHTMLFile(UploadedFile):
    '''Represent an uploaded HTML file

    While uploading an HTML file, several tags, attributee have to be deleted,
    because they would break KiwiTestPad's internal JavaScript features and styles
    and make some features unusable. Especially to the JavaScript surrounded by
    SCRIPT or referenced from unknown external resources, security issue must
    be considered.

    Currently, tags SCRIPT, STYLE AND LINK are removed. And attributes class,
    style and id are removed.
    '''

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

        return unicode(soup.body)


class UploadedODTFile(UploadedFile):
    '''Represent an uploaded ODT file'''

    def get_content(self):
        generatecss = True
        embedable = True
        odhandler = ODF2XHTML(generatecss, embedable)

        doc = load(self.uploaded_file)
        return odhandler.odf2xhtml(doc)


class PlanFileField(forms.FileField):
    VALID_CONTENT_TYPES = (MIMETYPE_HTML,
                           MIMETYPE_PLAIN,
                           MIMETYPE_OCTET_STREAM,
                           MIMETYPE_OPENDOCUMENT)
    ODT_CONTENT_TYPES = (MIMETYPE_OCTET_STREAM, MIMETYPE_OPENDOCUMENT)

    default_error_messages = {
        'invalid_file_type': 'The file you uploaded is not a correct, '
                             'Html/Plain text/ODT file.',
        'unexcept_odf_error': 'Unable to analyse the file or the file you '
                              'upload is not Open Document.',
        'unexpected_html_error': 'Invalid HTML document.',
    }

    def clean(self, data, initial=None):
        f = super(PlanFileField, self).clean(data, initial)
        if f is None:
            return None
        elif not data and initial:
            return initial

        if data.content_type not in self.VALID_CONTENT_TYPES:
            raise forms.ValidationError(
                self.error_messages['invalid_file_type'])

        if data.content_type in self.ODT_CONTENT_TYPES:
            try:
                return UploadedODTFile(data).get_content()
            except:
                raise forms.ValidationError(
                    self.error_messages['unexcept_odf_error'])

        if data.content_type == MIMETYPE_HTML:
            try:
                return UploadedHTMLFile(data).get_content()
            except:
                raise forms.ValidationError(
                    self.error_messages['unexpected_html_error'])

        if data.content_type == MIMETYPE_PLAIN:
            return UploadedPlainTextFile(data).get_content()


class CasePlanXMLField(forms.FileField):
    """
    Custom field for the XML file.
    Based on ImageField built-in Django source code.
    """
    default_error_messages = {
        'invalid_file': 'The file you uploaded is not a correct XML file.',
        'interpret_error': 'The file you uploaded unable to interpret.',
    }

    def process_case(self, case):
        try:
            return process_case(case)
        except ValueError as err:
            forms.ValidationError(err.message)

    def clean(self, data, initial=None):
        """
        Check the file content type is XML or not
        """
        f = super(CasePlanXMLField, self).clean(data, initial)
        if f is None:
            return None
        elif not data and initial:
            return initial

        if not data.content_type == 'text/xml' and not data.content_type == 'application/xml':
            raise forms.ValidationError(self.error_messages['invalid_file'])

        # We need to get a file object for PIL. We might have a path or we
        # might have to read the data into memory.
        if hasattr(data, 'temporary_file_path'):
            xml_file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                xml_file = data.read()
            else:
                xml_file = data['content']

        # Insert clean code here
        try:
            new_case_from_xml = clean_xml_file(xml_file)
        except ValueError as error:
            raise forms.ValidationError(error)
        except Exception as error:
            raise forms.ValidationError('%s: %s' % (
                self.error_messages['interpret_error'],
                error
            ))
        except SyntaxError as error:
            raise forms.ValidationError('%s: %s' % (
                self.error_messages['interpret_error'],
                error
            ))

        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)

        return new_case_from_xml


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
        queryset=TestPlanType.objects.all(),
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
        queryset=TCMSEnvGroup.get_active().all(),
        required=False
    )
    parent = forms.IntegerField(required=False)

    owner = forms.CharField(
        label="Plan Document",
        required=False
    )

    def clean_parent(self):
        try:
            p = self.cleaned_data['parent']
            if p:
                return TestPlan.objects.get(pk=p)
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
    notify_on_plan_delete = forms.BooleanField(
        label=' when plan is deleted',
        required=False
    )

    def clean_tag(self):
        return TestTag.objects.filter(
            name__in=TestTag.string_to_list(self.cleaned_data['tag'])
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
        queryset=TestPlanType.objects.all(),
        required=False,
    )
    env_group = forms.ModelChoiceField(
        label="Environment Group",
        queryset=TCMSEnvGroup.get_active().all(),
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
        from tcms.core.utils import string_to_list

        results = string_to_list(self.cleaned_data['pk__in'])
        try:
            return [int(r) for r in results]
        except Exception, e:
            raise forms.ValidationError(str(e))

    def clean_tag__name__in(self):
        return TestTag.string_to_list(self.cleaned_data['tag__name__in'])

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
        queryset=TestPlanType.objects.all(),
        required=False,
    )
    keep_orignal_author = forms.BooleanField(
        label='Keep orignal author',
        help_text='Unchecking will make me the author of the copied plan',
        required=False,
    )
    copy_texts = forms.BooleanField(
        label='Copy Plan Document',
        help_text='Check it to copy texts of the plan.',
        required=False,
    )
    copy_attachements = forms.BooleanField(
        label='Copy Plan Attachments',
        help_text='Check it to copy attachments of the plan.',
        required=False
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
        queryset=TestPlanType.objects.all(),
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


# =========== Mist forms ==============


class ImportCasesViaXMLForm(forms.Form):
    a = forms.CharField(widget=forms.HiddenInput)
    xml_file = CasePlanXMLField(
        label='Upload XML file:',
        help_text='XML file is exported from Kiwi or Testopia.'
    )


class PlanComponentForm(forms.Form):
    plan = forms.ModelMultipleChoiceField(
        label='',
        queryset=TestPlan.objects.none(),
        widget=forms.Select(attrs={'style': 'display:none;'}),
    )
    component = forms.ModelMultipleChoiceField(
        queryset=Component.objects.none(),
        required=False,
    )

    def __init__(self, tps, **kwargs):
        tp_ids = tps.values_list('pk', flat=True)
        product_ids = list(set(tps.values_list('product_id', flat=True)))

        if kwargs.get('initial'):
            kwargs['initial']['plan'] = tp_ids

        super(PlanComponentForm, self).__init__(**kwargs)

        self.fields['plan'].queryset = tps
        self.fields['component'].queryset = Component.objects.filter(
            product__pk__in=product_ids
        )
