# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html


from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from tcms.bugs.models import Bug
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
        return context


@method_decorator(permission_required('bugs.add_bug'), name='dispatch')
class New(TemplateView):
    template_name = 'bugs/mutable.html'

    def get(self, request, *args, **kwargs):
        form = NewBugForm()

        context_data = {
            'form': form,
        }

        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        form = NewBugForm(request.POST)

        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        else:
            form.populate()

        if form.is_valid():
            form.cleaned_data['reporter'] = request.user

            # todo: this must be coming from Product/Component QA owner
            # but user should be able to change it
            if not form.cleaned_data['assignee']:
                form.cleaned_data['assignee'] = request.user

            text = form.cleaned_data['text']
            del form.cleaned_data['text']

            bug = Bug.objects.create(**form.cleaned_data)
            add_comment([bug], text, request.user)

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
