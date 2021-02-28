# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView
from guardian.decorators import permission_required as object_permission_required

from tcms.testcases.forms import (
    CaseNotifyFormSet,
    CloneCaseForm,
    SearchCaseForm,
    TestCaseForm,
)
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan


def plan_from_request_or_none(request):  # pylint: disable=missing-permission-required
    """Get TestPlan from REQUEST

    This method relies on the existence of from_plan within REQUEST.
    """
    test_plan_id = request.POST.get("from_plan") or request.GET.get("from_plan")
    if not test_plan_id:
        return None
    return get_object_or_404(TestPlan, pk=test_plan_id)


@method_decorator(permission_required("testcases.add_testcase"), name="dispatch")
class NewCaseView(CreateView):
    model = TestCase
    form_class = TestCaseForm
    template_name = "testcases/mutable.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # clear fields which are set dynamically via JavaScript
        form.populate(self.request.POST.get("product", -1))
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"].update(  # pylint: disable=objects-update-used
            {
                "author": self.request.user,
            }
        )

        test_plan = plan_from_request_or_none(self.request)
        if test_plan:
            kwargs["initial"]["product"] = test_plan.product_id

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_plan"] = plan_from_request_or_none(self.request)
        context["notify_formset"] = kwargs.get("notify_formset") or CaseNotifyFormSet()
        return context

    def form_valid(self, form):
        test_plan = plan_from_request_or_none(self.request)

        notify_formset = CaseNotifyFormSet(self.request.POST)
        if notify_formset.is_valid():
            test_case = form.save()
            if test_plan:
                test_plan.add_case(test_case)

            notify_formset.instance = test_case
            notify_formset.save()

            return HttpResponseRedirect(reverse("testcases-get", args=[test_case.pk]))

        # taken from FormMixin.form_invalid()
        return self.render_to_response(
            self.get_context_data(notify_formset=notify_formset)
        )


@method_decorator(permission_required("testcases.view_testcase"), name="dispatch")
class TestCaseSearchView(TemplateView):
    """
    Shows the search form which uses JSON RPC to fetch the results
    """

    template_name = "testcases/search.html"

    def get_context_data(self, **kwargs):
        form = SearchCaseForm(self.request.GET)
        if self.request.GET.get("product"):
            form.populate(product_id=self.request.GET["product"])
        else:
            form.populate()

        return {
            "form": form,
        }


@method_decorator(
    object_permission_required(
        "testcases.view_testcase", (TestCase, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class TestCaseGetView(DetailView):

    model = TestCase
    template_name = "testcases/get.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["executions"] = self.object.executions.select_related(
            "run", "tested_by", "assignee", "case", "status"
        ).order_by("run__plan", "run")
        context["OBJECT_MENU_ITEMS"] = [
            (
                "...",
                [
                    (
                        _("Edit"),
                        reverse("testcases-edit", args=[self.object.pk]),
                    ),
                    (
                        _("Clone"),
                        reverse("testcases-clone") + "?case=%d" % self.object.pk,
                    ),
                    (
                        _("History"),
                        "/admin/testcases/testcase/%d/history/" % self.object.pk,
                    ),
                    ("-", "-"),
                    (
                        _("Object permissions"),
                        reverse(
                            "admin:testcases_testcase_permissions",
                            args=[self.object.pk],
                        ),
                    ),
                    ("-", "-"),
                    (
                        _("Delete"),
                        reverse(
                            "admin:testcases_testcase_delete",
                            args=[self.object.pk],
                        ),
                    ),
                ],
            )
        ]

        return context


@method_decorator(
    object_permission_required(
        "testcases.change_testcase", (TestCase, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class EditTestCaseView(UpdateView):

    model = TestCase
    template_name = "testcases/mutable.html"
    form_class = TestCaseForm

    def form_valid(self, form):
        notify_formset = CaseNotifyFormSet(self.request.POST, instance=self.object)
        if notify_formset.is_valid():
            notify_formset.save()
            return super().form_valid(form)

        # taken from FormMixin.form_invalid()
        return self.render_to_response(
            self.get_context_data(notify_formset=notify_formset)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notify_formset"] = kwargs.get("notify_formset") or CaseNotifyFormSet(
            instance=self.object
        )
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.POST.get("product"):
            form.populate(product_id=self.request.POST["product"])
        else:
            form.populate(product_id=self.object.category.product_id)
        return form

    def get_initial(self):
        default_tester = None
        if self.object.default_tester_id:
            default_tester = self.object.default_tester.email

        return {
            "product": self.object.category.product_id,
            "default_tester": default_tester,
        }


@method_decorator(permission_required("testcases.add_testcase"), name="dispatch")
class CloneTestCaseView(View):
    """Clone one case or multiple case into other plan or plans"""

    template_name = "testcases/clone.html"
    http_method_names = ["get", "post"]

    def post(self, request):
        if not self._is_request_data_valid(request):
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        # Do the clone action
        clone_form = CloneCaseForm(request.POST)
        clone_form.populate(case_ids=request.POST.getlist("case"))

        if clone_form.is_valid():
            for tc_src in clone_form.cleaned_data["case"]:
                tc_dest = tc_src.clone(request.user, clone_form.cleaned_data["plan"])

            # Detect the number of items and redirect to correct one
            if len(clone_form.cleaned_data["case"]) == 1:
                return HttpResponseRedirect(
                    reverse(
                        "testcases-get",
                        args=[
                            tc_dest.pk,
                        ],
                    )
                )

            if len(clone_form.cleaned_data["plan"]) == 1:
                test_plan = clone_form.cleaned_data["plan"][0]
                return HttpResponseRedirect(
                    reverse("test_plan_url_short", args=[test_plan.pk])
                )

            # Otherwise tell the user the clone action is successful
            messages.add_message(
                request, messages.SUCCESS, _("TestCase cloning was successful")
            )
            return HttpResponseRedirect(reverse("plans-search"))

        # invalid form
        messages.add_message(request, messages.ERROR, clone_form.errors)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    def get(self, request):
        if not self._is_request_data_valid(request):
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        # Initialize the clone case form
        clone_form = CloneCaseForm(request.GET)
        clone_form.populate(case_ids=request.GET.getlist("case"))

        context = {
            "form": clone_form,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def _is_request_data_valid(request):
        request_data = getattr(request, request.method)

        if "case" not in request_data:
            messages.add_message(
                request, messages.ERROR, _("At least one TestCase is required")
            )
            return False

        return True
