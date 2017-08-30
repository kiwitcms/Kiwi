# -*- coding: utf-8 -*-
from django.urls import reverse


def get_form():
    from .forms import SimpleForm
    return SimpleForm


def get_form_target():
    """
    Returns the target URL for the comment form submission view.
    """
    return reverse('comments-post')
