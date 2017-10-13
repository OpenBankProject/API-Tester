# -*- coding: utf-8 -*-
"""
URLs for runtests app
"""

from django.conf.urls import url

from .views import IndexView, RunView

urlpatterns = [
    url(r'^$',
        IndexView.as_view(),
        name='runtests-index'),
    url(r'^run/(?P<test>.+)',
        RunView.as_view(),
        name='runtests-run'),
]
