# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView
from guardian.decorators import permission_required as object_permission_required

from tcms.core.contrib.linkreference.forms import LinkReferenceForm
from tcms.core.forms import SimpleCommentForm
from tcms.testcases.models import BugSystem, TestCase, TestCasePlan, TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import NewRunForm, SearchRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun

User = get_user_model()  # pylint: disable=invalid-name


@method_decorator(permission_required("testruns.add_testrun"), name="dispatch")
class NewTestRunView(View):
    """Display new test run page."""

    template_name = "testruns/mutable.html"
    http_method_names = ["post", "get"]

    def get(self, request, form_initial=None, is_cloning=False):
        plan_id = request.GET.get("p")

        # note: ordered by pk for test_show_create_new_run_page()
        test_cases = (
            TestCase.objects.filter(pk__in=request.GET.getlist("c"))
            .select_related("author", "case_status", "category", "priority")
            .order_by("pk")
        )

        test_plan = TestPlan.objects.filter(pk=plan_id).first()
        if not form_initial:
            form_initial = {
                "summary": "Test run for %s" % test_plan.name if test_plan else "",
                "manager": test_plan.author.email if test_plan else "",
                "default_tester": request.user.email,
                "notes": "",
                "plan": plan_id,
            }

        form = NewRunForm(initial=form_initial)
        form.populate(plan_id)

        context_data = {
            "plan_id": plan_id,  # used for UI conditionals
            "test_cases": test_cases,
            "form": form,
            "disabled_cases": get_disabled_test_cases_count(test_cases),
            "is_cloning": is_cloning,
        }
        return render(request, self.template_name, context_data)

    def post(self, request):
        form = NewRunForm(data=request.POST)
        form.populate(request.POST.get("plan"))

        if form.is_valid():
            test_run = form.save()
            loop = 1

            for case in form.cleaned_data["case"]:
                try:
                    tcp = TestCasePlan.objects.get(
                        plan=form.cleaned_data["plan"], case=case
                    )
                    sortkey = tcp.sortkey
                except ObjectDoesNotExist:
                    sortkey = loop * 10

                test_run.create_execution(
                    case=case,
                    sortkey=sortkey,
                    assignee=form.cleaned_data["default_tester"],
                )
                loop += 1

            return HttpResponseRedirect(
                reverse(
                    "testruns-get",
                    args=[
                        test_run.pk,
                    ],
                )
            )

        test_cases = (
            TestCase.objects.filter(pk__in=request.POST.getlist("case"))
            .select_related("author", "case_status", "category", "priority")
            .order_by("pk")
        )

        context_data = {
            "plan_id": request.POST.get("plan"),
            "test_cases": test_cases,
            "form": form,
            "disabled_cases": get_disabled_test_cases_count(test_cases),
        }

        return render(request, self.template_name, context_data)


@method_decorator(permission_required("testruns.view_testrun"), name="dispatch")
class SearchTestRunView(TemplateView):

    template_name = "testruns/search.html"

    def get_context_data(self, **kwargs):
        form = SearchRunForm(self.request.GET)
        form.populate(product_id=self.request.GET.get("product"))

        return {
            "form": form,
        }


@method_decorator(
    object_permission_required(
        "testruns.view_testrun", (TestRun, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class GetTestRunView(DetailView):

    template_name = "testruns/get.html"
    http_method_names = ["get"]
    model = TestRun

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["execution_statuses"] = TestExecutionStatus.objects.order_by(
            "-weight", "name"
        )
        context["confirmed_statuses"] = TestCaseStatus.objects.filter(is_confirmed=True)
        context["link_form"] = LinkReferenceForm()
        context["bug_trackers"] = BugSystem.objects.all()
        context["comment_form"] = SimpleCommentForm()
        context["OBJECT_MENU_ITEMS"] = [
            (
                "...",
                [
                    (
                        _("Edit"),
                        reverse("testruns-edit", args=[self.object.pk]),
                    ),
                    (
                        _("Clone"),
                        reverse("testruns-clone", args=[self.object.pk]),
                    ),
                    (
                        _("History"),
                        "/admin/testruns/testrun/%d/history/" % self.object.pk,
                    ),
                    ("-", "-"),
                    (
                        _("Object permissions"),
                        reverse(
                            "admin:testruns_testrun_permissions",
                            args=[self.object.pk],
                        ),
                    ),
                    ("-", "-"),
                    (
                        _("Delete"),
                        reverse(
                            "admin:testruns_testrun_delete",
                            args=[self.object.pk],
                        ),
                    ),
                ],
            )
        ]

        return context


@method_decorator(
    object_permission_required(
        "testruns.change_testrun", (TestRun, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class EditTestRunView(UpdateView):
    model = TestRun
    template_name = "testruns/mutable.html"
    form_class = NewRunForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.populate(self.object.plan_id)

        return form

    def get_initial(self):
        return {
            "manager": self.object.manager,
            "default_tester": self.object.default_tester,
        }


@method_decorator(permission_required("testruns.add_testrun"), name="dispatch")
class CloneTestRunView(NewTestRunView):
    # note: post is handled directly by NewTestRunView
    # b/c <form action> points to testruns-new URL
    http_method_names = ["get"]

    def get(self, request, pk):  # pylint: disable=arguments-differ
        test_run = get_object_or_404(TestRun, pk=pk)

        request.GET._mutable = True  # pylint: disable=protected-access
        request.GET["p"] = test_run.plan_id
        request.GET.setlist(
            "c", test_run.executions.all().values_list("case", flat=True)
        )

        form_initial = {
            "summary": _("Clone of ") + test_run.summary,
            "notes": test_run.notes,
            "manager": test_run.manager,
            "build": test_run.build_id,
            "default_tester": test_run.default_tester,
            "plan": test_run.plan_id,
        }

        return super().get(request, form_initial=form_initial, is_cloning=True)


def get_disabled_test_cases_count(test_cases):
    return test_cases.filter(case_status__is_confirmed=False).count()
