# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from forms import SimpleForm


def get_form():
    return SimpleForm


def get_form_target():
    """
    Returns the target URL for the comment form submission view.
    """
    return reverse('comments-post')
