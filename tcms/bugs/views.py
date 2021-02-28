# Copyright (c) 2019-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html


from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView
from guardian.decorators import permission_required as object_permission_required

from tcms.bugs.forms import BugCommentForm, NewBugForm
from tcms.bugs.models import Bug
from tcms.core.helpers.comments import add_comment
from tcms.management.models import Component


@method_decorator(
    object_permission_required(
        "bugs.view_bug", (Bug, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class Get(DetailView):
    model = Bug
    template_name = "bugs/get.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = BugCommentForm()
        context["comment_form"].populate(self.object.pk)
        context["executions"] = self.object.executions.all()
        context["OBJECT_MENU_ITEMS"] = [
            (
                "...",
                [
                    (_("Edit"), reverse("bugs-edit", args=[self.object.pk])),
                    ("-", "-"),
                    (
                        _("Object permissions"),
                        reverse("admin:bugs_bug_permissions", args=[self.object.pk]),
                    ),
                    ("-", "-"),
                    (
                        _("Delete"),
                        reverse("admin:bugs_bug_delete", args=[self.object.pk]),
                    ),
                ],
            )
        ]

        return context


@method_decorator(permission_required("bugs.add_bug"), name="dispatch")
class New(CreateView):
    model = Bug
    form_class = NewBugForm
    template_name = "bugs/mutable.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("New bug")
        context["form_post_url"] = reverse("bugs-new")
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"].update(  # pylint: disable=objects-update-used
            {
                "reporter": self.request.user,
            }
        )
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # clear fields which are set dynamically via JavaScript
        form.populate(self.request.POST.get("product", -1))
        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        if not self.object.assignee:
            self.object.assignee = New.find_assignee(self.request.POST)
            self.object.save()
        add_comment([self.object], form.cleaned_data["text"], self.request.user)

        return response

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
        if "_execution" in data:
            assignee = New.assignee_from_components(
                data["_execution"].case.component.all()
            )
            del data["_execution"]

        if not assignee:
            assignee = New.assignee_from_components(
                Component.objects.filter(product=data["product"])
            )

        return assignee

    @staticmethod
    def create_bug(data):
        """
        Helper method used within Issue Tracker integration.

        :param data: Untrusted input, usually via HTTP request
        :type data: dict
        :return: bug
        :rtype: Model
        """
        bug = None

        if "assignee" not in data or not data["assignee"]:
            data["assignee"] = New.find_assignee(data)

        text = data["text"]
        del data["text"]

        bug = Bug.objects.create(**data)
        add_comment([bug], text, bug.reporter)

        return bug


@method_decorator(
    object_permission_required(
        "bugs.change_bug", (Bug, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class Edit(UpdateView):
    model = Bug
    form_class = NewBugForm
    template_name = "bugs/mutable.html"
    _values_before_update = {}

    def _record_changes(self, new_data):
        result = ""
        for field in self.model._meta.fields:
            field = field.name
            if (
                field in new_data
                and self._values_before_update[field] != new_data[field]
            ):
                result += "%s: %s -> %s\n" % (
                    field.title(),
                    self._values_before_update[field],
                    new_data[field],
                )
        if result:
            add_comment([self.object], result, self.request.user)

    def get_initial(self):
        return {
            "assignee": self.object.assignee,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Edit bug")
        context["form_post_url"] = reverse(
            "bugs-edit",
            args=[
                self.object.pk,
            ],
        )
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        for field in self.model._meta.fields:
            self._values_before_update[field.name] = getattr(obj, field.name)
        return obj

    def form_valid(self, form):
        self._record_changes(form.cleaned_data)
        return super().form_valid(form)


@method_decorator(permission_required("django_comments.add_comment"), name="dispatch")
class AddComment(View):
    http_methods = ["post"]

    def post(self, request):
        form = BugCommentForm(request.POST)
        request_action = request.POST.get("action")

        if form.is_valid():
            bug = form.cleaned_data["bug"]
            if form.cleaned_data["text"]:
                add_comment([bug], form.cleaned_data["text"], request.user)

            if request_action == "close":
                bug.status = False
                add_comment([bug], _("*bug closed*"), request.user)

            if request_action == "reopen":
                bug.status = True
                add_comment([bug], _("*bug reopened*"), request.user)
            bug.save()

        return HttpResponseRedirect(reverse("bugs-get", args=[bug.pk]))


@method_decorator(permission_required("bugs.view_bug"), name="dispatch")
class Search(TemplateView):
    template_name = "bugs/search.html"

    def get_context_data(self, **kwargs):
        form = NewBugForm(self.request.GET)
        form.populate(self.request.GET.get("product", -1))

        return {"form": form}
