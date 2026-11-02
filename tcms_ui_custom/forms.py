from django import forms
from tcms.kiwi_auth.forms import RegistrationForm
from tcms.management.models import Product, Component, Priority, Tag
from tcms.testcases.models import TestCase, Category, TestCaseStatus

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag Name'}),
        }

class TestCaseForm(forms.ModelForm):
    # Fields not native to Kiwi's TestCase model
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    pre_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    post_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    # Tags as a multi-select dropdown
    tags_input = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'id': 'id_tags_input'})
    )

    component = forms.ModelChoiceField(
        queryset=Component.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    case_status = forms.ModelChoiceField(
        queryset=TestCaseStatus.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TestCase
        fields = ['summary']
        widgets = {
            'summary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title of the test case'}),
        }

class CustomRegistrationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
