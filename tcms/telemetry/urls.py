from django.conf.urls import url

from tcms.telemetry import views

urlpatterns = [
    url(r'^testing/breakdown/$', views.TestingBreakdownView.as_view(), name='testing-breakdown'),
    url(r'^testing/status-matrix/$', views.TestingStatusMatrixView.as_view(),
        name='testing-status-matrix')
]
