# -*- coding: utf-8 -*-
def test_template(request, template_name):
    """
    Test the template appearence
    """
    from django.shortcuts import render_to_response
    from django.template import RequestContext

    return render_to_response(template_name, RequestContext(request))
