from django.conf.urls import url

from tcms.telemetry.views import TestingBreakdownView

urlpatterns = [
    url(r'^testing/breakdown/$', TestingBreakdownView.as_view(), name='testing-breakdown')
]
