# -*- coding: utf-8 -*-
import os
import subprocess  # nosec:B404:import_subprocess
import time

from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.template import loader
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.utils.translation import trans_real
from django.views import i18n
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic.base import TemplateView, View

from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun


@method_decorator(
    login_required, name="dispatch"
)  # pylint: disable=missing-permission-required
class DashboardView(TemplateView):

    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """List all recent TestPlans and TestRuns"""
        test_plans = (
            TestPlan.objects.filter(author=self.request.user)
            .order_by("-pk")
            .select_related("product", "type")
            .annotate(num_runs=Count("run", distinct=True))
        )
        test_plans_disable_count = test_plans.filter(is_active=False).count()

        test_runs = (
            TestRun.objects.filter(
                Q(manager=self.request.user)
                | Q(default_tester=self.request.user)
                | Q(executions__assignee=self.request.user),
                stop_date__isnull=True,
            )
            .order_by("-pk")
            .distinct()
        )

        return {
            "test_plans_count": test_plans.count(),
            "test_plans_disable_count": test_plans_disable_count,
            "last_15_test_plans": test_plans.filter(is_active=True)[:15],
            "last_15_test_runs": test_runs[:15],
            "test_runs_count": test_runs.count(),
        }


@requires_csrf_token
def server_error(request):  # pylint: disable=missing-permission-required
    """
    Render the error page with request object which supports
    static URLs so we can load a nice picture.
    """
    template = loader.get_template("500.html")
    return http.HttpResponseServerError(template.render({}, request))


class IterOpen(subprocess.Popen):  # pylint: disable=missing-permission-required
    """
    Popen which allows us to iterate over the output so we can
    stream it back to the browser with some extra eye candy!
    """

    still_waiting = True
    has_completed = False

    @property
    def timestamp(self):
        return timezone.now().isoformat().replace("T", " ") + " init-db: "

    def __iter__(self):
        os.set_blocking(self.stdout.fileno(), False)
        return self

    def __next__(self):
        line = self.stdout.readline()

        if not line:
            if self.still_waiting:
                time.sleep(3)
                return self.timestamp + "waiting for migrations to start\n"

            if not self.has_completed:
                self.has_completed = True
                return self.timestamp + "Complete!\n"

            # instruct the streaming response to stop streaming
            raise StopIteration

        self.still_waiting = False
        return self.timestamp + line.lstrip()


class InitDBView(TemplateView):  # pylint: disable=missing-permission-required

    template_name = "initdb.html"

    def post(self, request):
        # Default production installation
        manage_path = "/Kiwi/manage.py"
        if not os.path.exists(manage_path):
            # Development installation
            manage_path = os.path.join(settings.TCMS_ROOT_PATH, "..", "manage.py")

        if "init_db" in request.POST:
            # Perform migrations
            proc = IterOpen(
                [manage_path, "migrate"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,  # line buffered
                universal_newlines=True,
            )
            response = StreamingHttpResponse(
                proc, content_type="text/plain; charset=utf-8"
            )
            response["Cache-Control"] = "no-cache"
            return response

        return HttpResponseRedirect(reverse("init-db"))


class TranslationMode(View):  # pylint: disable=missing-permission-required
    """
    Turns on and off translation mode by switching language to
    Esperanto!
    """

    @staticmethod
    def get_browser_language(request):
        """
        Returns *ONLY* the language that is sent by the browser via the
        Accept-Language headers. Defaults to ``settings.LANGUAGE_CODE`` if
        that doesn't work!

        This is the language we switch back to when translation mode is turned off.

        Copied from the bottom half of
        ``django.utils.translation.trans_real.get_language_from_request()``

        .. note::

            Using ``get_language_from_request()`` doesn't work for us because
            it first inspects session and cookies and we've already set Esperanto
            in both the session and the cookie!
        """
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        for accept_lang, _unused in trans_real.parse_accept_lang_header(accept):
            if accept_lang == "*":
                break

            if not trans_real.language_code_re.search(accept_lang):
                continue

            try:
                return translation.get_supported_language_variant(accept_lang)
            except LookupError:
                continue

        try:
            return translation.get_supported_language_variant(settings.LANGUAGE_CODE)
        except LookupError:
            return settings.LANGUAGE_CODE

    def get(self, request):
        """
        In the HTML template we'd like to work with simple links
        however the view which actually switches the language needs
        to be called via POST so we simulate that here!

        If the URL doesn't explicitly specify language then we turn-off
        translation mode by switching back to browser preferred language.
        """
        browser_lang = self.get_browser_language(request)
        post_body = "%s=%s" % (
            i18n.LANGUAGE_QUERY_PARAMETER,
            request.GET.get(i18n.LANGUAGE_QUERY_PARAMETER, browser_lang),
        )
        request.META["REQUEST_METHOD"] = "POST"
        request.META["CONTENT_LENGTH"] = len(post_body)
        request.META["CONTENT_TYPE"] = "application/x-www-form-urlencoded"

        post_request = request.__class__(request.META)
        # pylint: disable=protected-access
        post_request._post = http.QueryDict(post_body, encoding=post_request._encoding)

        return i18n.set_language(post_request)
