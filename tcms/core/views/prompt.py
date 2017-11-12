# -*- coding: utf-8 -*-
# FIXME: Use exception to replace the feature

from django.shortcuts import render


class Prompt(object):
    """Common dialog to prompt to users"""

    Alert = 'alert'
    Info = 'info'

    def __init__(self, request, info_type=None, info=None, next=None):
        super(Prompt, self).__init__()
        self.request = request
        self.info_type = info_type
        self.info = info
        self.next = next

    @classmethod
    def render(cls, request, info_type=None, info=None, next=None):
        """Generate the html to response"""
        return render(request, 'prompt.html', context={
            'type': info_type,
            'info': info,
            'next': next
        })
