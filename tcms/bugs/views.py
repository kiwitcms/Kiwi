# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html


from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from tcms.bugs.models import Bug
from tcms.management.models import Component
from tcms.bugs.forms import NewBugForm, BugCommentForm
from tcms.core.helpers.comments import add_comment


class Get(DetailView):  # pylint: disable=missing-permission-required
    model = Bug
    template_name = 'bugs/get.html'
    http_method_names = ['get']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = BugCommentForm()
        context['comment_form'].populate(self.object.pk)
        context['executions'] = self.object.executions.all()

        return context


@method_decorator(permission_required('bugs.add_bug'), name='dispatch')
class New(TemplateView):
    template_name = 'bugs/mutable.html'

    @staticmethod
    def assignee_from_components(components):
        """
            Return the first owner which is assigned to any of the
            components. This is as best as we can to automatically figure
            out who should be assigned to this bug.
        """
        for component in components:
            if component.initial_owner:
                return component.initial_owner

        return None

    @staticmethod
    def find_assignee(data):
        """
            Try to automatically find an assignee for Bug by first scanning
            TestCase components (if present) and then components for the
            product.
        """
        assignee = None
        if '_execution' in data:
            assignee = New.assignee_from_components(data['_execution'].case.component.all())
            del data['_execution']

        if not assignee:
            assignee = New.assignee_from_components(
                Component.objects.filter(product=data['product']))

        return assignee

    @staticmethod
    def create_bug(data, user):
        """
            Helper method used to create new bug. Also used within
            Issue Tracker integration.

            :param data: Untrusted input, usually via HTTP request
            :type data: dict
            :param user: An instance of User object
            :return: (form, bug)
            :rtype: tuple
        """
        bug = None
        assignee = New.find_assignee(data)
        form = NewBugForm(data)

        if data.get('product'):
            form.populate(data['product'])
        else:
            form.populate()

        if form.is_valid():
            form.cleaned_data['reporter'] = user

            if not form.cleaned_data['assignee']:
                form.cleaned_data['assignee'] = assignee

            text = form.cleaned_data['text']
            del form.cleaned_data['text']

            bug = Bug.objects.create(**form.cleaned_data)
            add_comment([bug], text, user)

        return form, bug

    def get(self, request, *args, **kwargs):
        form = NewBugForm()

        context_data = {
            'form': form,
        }

        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        form, bug = self.create_bug(request.POST, request.user)

        if bug:
            return HttpResponseRedirect(reverse('bugs-get', args=[bug.pk]))

        context_data = {
            'form': form,
        }

        return render(request, self.template_name, context_data)


@method_decorator(permission_required('django_comments.add_comment'), name='dispatch')
class AddComment(View):
    http_methods = ['post']

    def post(self, request, *args, **kwargs):
        form = BugCommentForm(request.POST)

        if form.is_valid():
            bug = form.cleaned_data['bug']
            add_comment([bug], form.cleaned_data['text'], request.user)

        return HttpResponseRedirect(reverse('bugs-get', args=[bug.pk]))


class Search(View):  # pylint: disable=missing-permission-required
    pass
