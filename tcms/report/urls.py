# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='overall/', permanent=True)),
    url(r'^overall/$', views.overall, name='report-overall'),
    url(r'^product/(?P<product_id>\d+)/overview/$', views.overview, name='report-overview'),
    url(r'^product/(?P<product_id>\d+)/build/$', views.ProductBuildReport.as_view(),
        name='report-overall-product-build'),
    url(r'^product/(?P<product_id>\d+)/version/$', views.ProductVersionReport.as_view(),
        name='report-overall-product-version'),
    url(r'^product/(?P<product_id>\d+)/component/$', views.ProductComponentReport.as_view(),
        name='report-overall-product-component'),
    url(r'custom/$', views.CustomReport.as_view(), name='report-custom'),
    url(r'^custom/details/$', views.CustomDetailReport.as_view(), name='report-custom-details'),

    url(r'^testing/$', views.TestingReport.as_view(), name='testing-report'),
    url(r'^testing/case-runs/$', views.TestingReportCaseRuns.as_view(),
        name='testing-report-case-runs'),
]
