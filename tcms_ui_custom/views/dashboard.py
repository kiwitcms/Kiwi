from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tcms.management.models import Product
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestExecution

@login_required
def dashboard(request):
    context = {
        'total_projects': Product.objects.count(),
        'total_testcases': TestCase.objects.count(),
        'active_plans': TestPlan.objects.filter(is_active=True).count(),
        'recent_failures': TestExecution.objects.filter(
            status__name__in=['FAIL', 'BLOCKED']
        ).order_by('-id')[:5],
        'jira_sidebar_products': Product.objects.all().order_by('name')
    }
    return render(request, 'dashboard.html', context)
