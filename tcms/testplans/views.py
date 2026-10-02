# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from guardian.decorators import permission_required as object_permission_required

from tcms.core.forms import SimpleCommentForm
from tcms.management.models import Priority
from tcms.testcases.models import TestCaseStatus
from tcms.testplans.forms import (
    ClonePlanForm,
    NewPlanForm,
    PlanNotifyFormSet,
    SearchPlanForm,
)
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun


@method_decorator(permission_required("testplans.add_testplan"), name="dispatch")
class NewTestPlanView(CreateView):
    model = TestPlan
    form_class = NewPlanForm
    template_name = "testplans/mutable.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # clear fields which are set dynamically via JavaScript
        form.populate(self.request.POST.get("product", -1))
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"]["author"] = self.request.user
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notify_formset"] = kwargs.get("notify_formset") or PlanNotifyFormSet()
        return context

    def form_valid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST)
        if notify_formset.is_valid():
            test_plan = form.save()
            notify_formset.instance = test_plan
            notify_formset.save()

            return HttpResponseRedirect(test_plan.get_absolute_url())

        # taken from FormMixin.form_invalid()
        return self.render_to_response(
            self.get_context_data(notify_formset=notify_formset)
        )


@method_decorator(
    object_permission_required(
        "testplans.change_testplan", (TestPlan, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class Edit(UpdateView):
    model = TestPlan
    form_class = NewPlanForm
    template_name = "testplans/mutable.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.POST.get("product"):
            form.populate(product_id=self.request.POST["product"])
        else:
            form.populate(product_id=self.object.product_id)
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notify_formset"] = kwargs.get("notify_formset") or PlanNotifyFormSet(
            instance=self.object
        )
        return context

    def form_valid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST, instance=self.object)
        if notify_formset.is_valid():
            notify_formset.save()
            return super().form_valid(form)

        # taken from FormMixin.form_invalid()
        context_data = self.get_context_data(form=form, notify_formset=notify_formset)
        return self.render_to_response(context_data)

    def form_invalid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST, instance=self.object)
        context_data = self.get_context_data(form=form, notify_formset=notify_formset)
        return self.render_to_response(context_data)


@method_decorator(permission_required("testplans.view_testplan"), name="dispatch")
class SearchTestPlanView(TemplateView):
    template_name = "testplans/search.html"

    def get_context_data(self, **kwargs):
        form = SearchPlanForm(self.request.GET)
        form.populate(product_id=self.request.GET.get("product"))

        context_data = {
            "form": form,
        }

        return context_data


@method_decorator(
    object_permission_required(
        "testplans.view_testplan", (TestPlan, "pk", "pk"), accept_global_perms=True
    ),
    name="dispatch",
)
class TestPlanGetView(DetailView):
    template_name = "testplans/get.html"
    http_method_names = ["get"]
    model = TestPlan

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = TestCaseStatus.objects.all()
        context["priorities"] = Priority.objects.filter(is_active=True)
        context["comment_form"] = SimpleCommentForm()
        context["test_runs"] = TestRun.objects.filter(
            plan_id=self.object.pk, stop_date__isnull=True
        ).order_by("-id")[:5]
        context["OBJECT_MENU_ITEMS"] = [
            (
                "...",
                [
                    (_("Edit"), reverse("plan-edit", args=[self.object.pk])),
                    (_("Clone"), reverse("plans-clone", args=[self.object.pk])),
                    (
                        _("Deep clone"),
                        reverse("plans-clone", args=[self.object.pk]) + "?tree=1",
                    ),
                    (
                        _("History"),
                        f"/admin/testplans/testplan/{self.object.pk}/history/",
                    ),
                    ("-", "-"),
                    (
                        _("Object permissions"),
                        reverse(
                            "admin:testplans_testplan_permissions",
                            args=[self.object.pk],
                        ),
                    ),
                    ("-", "-"),
                    (
                        _("Delete"),
                        reverse(
                            "admin:testplans_testplan_delete",
                            args=[self.object.pk],
                        ),
                    ),
                ],
            )
        ]

        return context


@method_decorator(permission_required("testplans.add_testplan"), name="dispatch")
class Clone(TemplateView):
    """
    Renders the clone page. The TestPlan from the URL and the additional
    ones listed via the ``?p=`` query string arguments are cloned together,
    one form per TestPlan. The actual cloning is performed by the
    ``TestPlan.clone()`` RPC method, called from the browser, so that the
    page knows the IDs of the newly created TestPlans!
    See tcms/rpc/api/testplan.py

    When the ``?tree=1`` query string argument is present the whole sub-tree
    rooted at the TestPlan from the URL is rendered instead, in depth first
    order. The browser then clones every row and re-parents the newly created
    TestPlans so that the cloned tree mimics the source tree!
    """

    template_name = "testplans/clone.html"

    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_tree = self.request.GET.get("tree") in ("1", "true", "on", "yes")
        context["is_tree"] = is_tree

        objects = self.get_clone_objects(is_tree)

        rows = []
        path = []
        for index, plan in enumerate(objects):
            if is_tree:
                self.augment_with_tree_prefix(plan, path, objects, index)

            rows.append((plan, self.make_clone_form(plan)))

        context["rows"] = rows
        return context

    def get_clone_objects(self, is_tree):
        if is_tree:
            # when ?tree=1 is given clone the whole sub-tree rooted at the
            # TestPlan from the URL instead, in depth first order, so that
            # every row appears after its parent
            tree_root = TestPlan.objects.with_tree_fields().get(pk=self.kwargs["pk"])
            return list(tree_root.descendants(include_self=True))

        # the TestPlan from the URL plus the additional ones specified via
        # the ?p= query string arguments. Duplicates are not a problem and
        # invalid values are ignored b/c they can never be cloned!
        pks = [self.kwargs["pk"]]
        for plan_id in self.request.GET.getlist("p"):
            try:
                pks.append(int(plan_id))
            except ValueError:
                continue

        return list(TestPlan.objects.filter(pk__in=pks).order_by("pk"))

    @staticmethod
    def augment_with_tree_prefix(plan, path, objects, index):
        plan.is_last_child = True
        for sibling in objects[index + 1 :]:
            if sibling.tree_depth < plan.tree_depth:
                break
            if sibling.tree_depth == plan.tree_depth:
                plan.is_last_child = False
                break

        # objects[0] is the root of the sub-tree being cloned
        depth = plan.tree_depth - objects[0].tree_depth
        del path[depth:]

        plan.tree_prefix = ""
        for level in range(1, depth):
            if path[level].is_last_child:
                plan.tree_prefix += "\u00a0\u00a0\u00a0"
            else:
                plan.tree_prefix += "│\u00a0\u00a0"
        if depth:
            plan.tree_prefix += "└─\u00a0" if plan.is_last_child else "├─\u00a0"

        path.append(plan)

    @staticmethod
    def make_clone_form(plan):
        form = ClonePlanForm(
            initial={
                "name": plan.make_cloned_name(),
                "product": plan.product,
                "version": plan.product_version,
            }
        )
        form.populate(product_pk=plan.product_id, parent_pk=plan.pk)
        return form
