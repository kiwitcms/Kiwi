# -*- coding: utf-8 -*-
from django.shortcuts import render


def test_template(request, template_name):
    """
    Test the template appearence
    """
    return render(request, template_name)
