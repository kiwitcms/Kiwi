# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import connection, models
from django.urls import reverse
from tree_queries.models import TreeNode

from tcms.core.history import KiwiHistoricalRecords
from tcms.core.models.base import UrlMixin
from tcms.core.templatetags.extra_filters import bleach_input
from tcms.management.models import Version
from tcms.testcases.models import TestCasePlan

# django-tree-queries declares the columns of its recursive CTE as char(1000)
# and MariaDB doesn't widen that type when the branches of the CTE are merged.
# tree_ordering grows by exactly 20 characters per level, a 20 character zero
# padded PK plus the separator, so it is the column which limits how deep a
# tree can be before it gets truncated. Truncated tree columns silently lose
# the depth first ordering, which breaks tree_view_html(), and raise DataError
# when sql_mode is strict, which breaks saving.
# See https://github.com/kiwitcms/Kiwi/issues/4334
TREE_COLUMN_WIDTH = 1000
TREE_ORDERING_CHARS_PER_LEVEL = 20

# The tree columns are compared as strings and MariaDB only compares the first
# max_sort_length bytes of a sort key, 1024 by default. Under utf8mb4
# collations the key is expanded to 2 bytes per character, so about 512
# characters are compared before two different paths look equal and the depth
# first ordering is lost.
TREE_SORTED_CHARS = 1024 // 2

# the maximum number of TestPlan objects on a single root to leaf path
MAX_TREE_NODES = (
    min(TREE_COLUMN_WIDTH - 1, TREE_SORTED_CHARS) // TREE_ORDERING_CHARS_PER_LEVEL
)


class PlanType(models.Model, UrlMixin):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class TestPlan(TreeNode, UrlMixin):
    """A plan within the TCMS"""

    history = KiwiHistoricalRecords()

    name = models.CharField(max_length=255, db_index=True)
    text = models.TextField(blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)
    extra_link = models.URLField(
        max_length=1024,
        default=None,
        blank=True,
        null=True,
        validators=[URLValidator(schemes=["http", "https", "ftp", "ftps"])],
    )

    product_version = models.ForeignKey(
        Version, related_name="plans", on_delete=models.CASCADE
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(
        "management.Product", related_name="plan", on_delete=models.CASCADE
    )
    type = models.ForeignKey(PlanType, on_delete=models.CASCADE)
    tag = models.ManyToManyField(
        "management.Tag", through="testplans.TestPlanTag", related_name="plan"
    )

    def __str__(self):
        return self.name

    def add_case(self, case, sortkey=None):
        if sortkey is None:
            lastcase = self.testcaseplan_set.order_by("-sortkey").first()
            if lastcase and lastcase.sortkey is not None:
                sortkey = lastcase.sortkey + 10
            else:
                sortkey = 0

        return TestCasePlan.objects.get_or_create(
            plan=self, case=case, defaults={"sortkey": sortkey}
        )[0]

    def add_tag(self, tag):
        return TestPlanTag.objects.get_or_create(plan=self, tag=tag)

    def remove_tag(self, tag):
        TestPlanTag.objects.filter(plan=self, tag=tag).delete()

    def delete_case(self, case):
        TestCasePlan.objects.filter(case=case.pk, plan=self.pk).delete()

    def _get_absolute_url(self):
        return reverse("test_plan_url", args=[self.pk])

    def get_absolute_url(self):
        return self._get_absolute_url()

    def get_full_url(self):
        return super().get_full_url().rstrip("/")

    def _get_email_conf(self):
        try:
            # note: this is the reverse_name of a 1-to-1 field
            return self.email_settings  # pylint: disable=no-member
        except ObjectDoesNotExist:
            return TestPlanEmailSettings.objects.create(plan=self)

    emailing = property(_get_email_conf)

    def make_cloned_name(self):
        return f"Clone of TP-{self.pk}: {self.name}"

    def clone(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name=None,
        product=None,
        version=None,
        new_author=None,
        parent=None,
        copy_testcases=False,
        **_kwargs,
    ):
        """Clone this plan

        :param name: New name of cloned plan. If not passed, make_cloned_name is called
            to generate a default one.
        :type name: str
        :param product: Product of cloned plan. If not passed, original plan's product is used.
        :type product: :class:`tcms.management.models.Product`
        :param version: Product version of cloned plan. If not passed use from source plan.
        :type version: :class:`tcms.management.models.Version`
        :param new_author: New author of cloned plan. If not passed, original plan's
            author is used.
        :type new_author: settings.AUTH_USER_MODEL
        :param parent: Parent of cloned plan. If not passed the cloned plan
            is created without a parent.
        :type parent: :class:`tcms.testplans.models.TestPlan`
        :param copy_testcases: Whether to copy cases to cloned plan instead of just
            linking them. Default is False.
        :type copy_testcases: bool
        :param \\**_kwargs: Unused catch-all variable container for any extra input
            which may be present
        :return: cloned plan
        :rtype: :class:`tcms.testplans.models.TestPlan`
        """
        tp_dest = TestPlan.objects.create(
            name=name or self.make_cloned_name(),
            product=product or self.product,
            author=new_author or self.author,
            type=self.type,
            product_version=version or self.product_version,
            create_date=self.create_date,
            is_active=self.is_active,
            extra_link=self.extra_link,
            parent=parent,
            text=self.text,
        )

        # Copy the plan tags
        for tp_tag_src in self.tag.all():
            tp_dest.add_tag(tag=tp_tag_src)

        # include TCs inside cloned TP
        qs = self.cases.all().annotate(sortkey=models.F("testcaseplan__sortkey"))
        for tc_src in qs:
            # this parameter should really be named clone_testcases b/c if set
            # it clones the source TC and then adds it to the new TP
            if copy_testcases:
                tc_src.clone(new_author, [tp_dest])
            else:
                # otherwise just link the existing TC to the new TP
                tp_dest.add_case(tc_src, sortkey=tc_src.sortkey)

        return tp_dest

    def tree_as_list(self):
        """
        Returns the entire tree family as a list of TestPlan
        object with additional fields from tree_queries!
        """
        plan = TestPlan.objects.with_tree_fields().get(pk=self.pk)

        tree_root = plan.ancestors(include_self=True).first()
        result = tree_root.descendants(include_self=True)

        return result

    def _parent_id_as_stored(self):
        """
        Returns the parent_id value currently stored in the database
        for the current object.
        """
        return (
            TestPlan.objects.filter(pk=self.pk)
            .values_list("parent_id", flat=True)
            .first()
        )

    def _count_nodes_on_longest_path(self):
        """
        Returns the number of TestPlan objects from the root of the tree
        down to the deepest descendant of the current object.
        """
        nodes = 1  # the current object

        parent_id = self.parent_id
        while parent_id is not None:
            nodes += 1
            parent_id = (
                TestPlan.objects.filter(pk=parent_id)
                .values_list("parent_id", flat=True)
                .first()
            )

        if self.pk is None:
            return nodes

        level = [self.pk]
        while True:
            level = list(
                TestPlan.objects.filter(parent_id__in=level).values_list(
                    "pk", flat=True
                )
            )
            if not level:
                break
            nodes += 1

        return nodes

    @staticmethod
    def tree_columns_are_truncated():
        if connection.vendor != "mysql":
            # other backends either use arrays for the tree columns or don't
            # have a width limitation at all
            return False

        # NOTE: if the server can't be interrogated assume MariaDB, which
        # truncates while MySQL widens the columns of recursive CTEs
        return getattr(connection, "mysql_is_mariadb", True)

    def clean(self):
        super().clean()

        if not self.tree_columns_are_truncated():
            return

        if not self._state.adding:
            # the depth of the current object and of its sub-tree changes only
            # when the parent changes. In that case the whole sub-tree is
            # taken into account by _count_nodes_on_longest_path() below
            if self.parent_id == self._parent_id_as_stored():
                return

        nodes = self._count_nodes_on_longest_path()
        if nodes > MAX_TREE_NODES:
            raise RuntimeError(
                f"A TestPlan tree can have at most {MAX_TREE_NODES} TestPlans "
                "on a single root to leaf path, otherwise the tree columns "
                "of django-tree-queries are truncated. See "
                "https://github.com/kiwitcms/Kiwi/issues/4334"
            )

    def tree_view_html(self):
        """
        Returns nested tree structure represented as Patterfly TreeView!
        Relies on the fact that tree nodes are returned in DFS
        order!
        """
        tree_nodes = self.tree_as_list()

        # TP is not part of a tree
        if len(tree_nodes) == 1:
            return ""

        result = ""
        previous_depth = -1

        for test_plan in tree_nodes:
            # close tags for previously rendered node before rendering current one
            if test_plan.tree_depth == previous_depth:
                result += """
                    </div><!-- end-subtree -->
                </div> <!-- end-node -->"""

            # indent
            previous_depth = max(test_plan.tree_depth, previous_depth)

            # outdent
            did_outdent = False
            while test_plan.tree_depth < previous_depth:
                result += """
                    </div><!-- end-subtree -->
                </div> <!-- end-node -->"""
                previous_depth -= 1
                did_outdent = True

            if did_outdent:
                result += """
                    </div><!-- end-subtree -->
                </div> <!-- end-node -->"""

            # render the current node
            active_class = ""
            if test_plan.pk == self.pk:
                active_class = "active"

            plan_name = bleach_input(test_plan.name)
            result += f"""
                <!-- begin-node -->
                <div class="list-group-item {active_class}" style="border: none">
                    <div class="list-group-item-header kiwi-padding-0">
                        <div class="list-view-pf-main-info kiwi-padding-0">
                            <div class="list-view-pf-left"
                                 style="margin-left:3px; padding-right:10px">
                                <span class="fa fa-angle-right"></span>
                            </div>

                            <div class="list-view-pf-body">
                                <div class="list-view-pf-description">
                                    <div class="list-group-item-text">
                                        <a href="{test_plan.get_absolute_url()}">
                                            TP-{test_plan.pk}: {plan_name}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div> <!-- /header -->

                    <!-- begin-subtree -->
                    <div class="list-group-item-container container-fluid" style="border: none">
            """

        # close after the last elements in the for loop
        while previous_depth >= 0:
            result += """
                    </div><!-- end-subtree -->
                </div> <!-- end-node -->"""
            previous_depth -= 1

        # HTML sanity check
        begin_node = result.count("<!-- begin-node -->")
        end_node = result.count("<!-- end-node -->")

        begin_subtree = result.count("<!-- begin-subtree -->")
        end_subtree = result.count("<!-- end-subtree -->")

        # tese will make sure that we catch errors in production
        if begin_node != end_node:
            raise RuntimeError("Begin/End count for tree-view nodes don't match")

        if begin_subtree != end_subtree:
            raise RuntimeError("Begin/End count for tree-view subtrees don't match")

        return f"""
            <div id="test-plan-family-tree"
                 class="list-group tree-list-view-pf kiwi-margin-top-0">
                {result}
            </div>
        """


class TestPlanTag(models.Model):
    tag = models.ForeignKey("management.Tag", on_delete=models.CASCADE)
    plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE)


class TestPlanEmailSettings(models.Model):
    plan = models.OneToOneField(
        TestPlan, related_name="email_settings", on_delete=models.CASCADE
    )
    auto_to_plan_author = models.BooleanField(default=True)
    auto_to_case_owner = models.BooleanField(default=True)
    auto_to_case_default_tester = models.BooleanField(default=True)
    notify_on_plan_update = models.BooleanField(default=True)
    notify_on_case_update = models.BooleanField(default=True)
