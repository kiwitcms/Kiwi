# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns
from django.views.generic.base import RedirectView

from .views import CustomDetailReport
from .views import CustomReport
from .views import ProductBuildReport
from .views import ProductComponentReport
from .views import ProductVersionReport
from .views import TestingReport
from .views import TestingReportCaseRuns

urlpatterns = patterns('tcms.report.views',
    url(r'^$', RedirectView.as_view(url='overall/', permanent=True)),
    url(r'^overall/$', 'overall'),
    url(r'^product/(?P<product_id>\d+)/overview/$', 'overview'),
    url(r'^product/(?P<product_id>\d+)/build/$', ProductBuildReport.as_view(),
        name='report-overall-product-build'),
    url(r'^product/(?P<product_id>\d+)/version/$', ProductVersionReport.as_view(),
        name='report-overall-product-version'),
    url(r'^product/(?P<product_id>\d+)/component/$', ProductComponentReport.as_view(),
        name='report-overall-product-component'),
    url(r'custom/$', CustomReport.as_view(), name='report-custom'),
    url(r'^custom/details/$', CustomDetailReport.as_view(), name='report-custom-details'),

    url(r'^testing/$', TestingReport.as_view(), name='testing-report'),
    url(r'^testing/case-runs/$', TestingReportCaseRuns.as_view(),
        name='testing-report-case-runs'),
)
