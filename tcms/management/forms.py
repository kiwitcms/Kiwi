# -*- coding: utf-8 -*-

from django import forms

from tcms.management.models import (
    Build,
    Classification,
    Component,
    Priority,
    Product,
    Tag,
    Version,
)


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"


class ClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = "__all__"


class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = "__all__"


class PriorityForm(forms.ModelForm):
    class Meta:
        model = Priority
        fields = "__all__"


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = "__all__"


class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = ["product", "value"]
