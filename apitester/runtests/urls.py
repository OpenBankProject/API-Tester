# -*- coding: utf-8 -*-
"""
URLs for runtests app
"""

from django.conf.urls import url

from .views import (
    IndexView,
    RunView,
    TestConfigurationCreateView,
    TestConfigurationUpdateView,
    TestConfigurationDeleteView
)

urlpatterns = [
    url(r'^$',
        IndexView.as_view(),
        name='runtests-index'),
    url(r'^(?P<testconfig_pk>[0-9]+)',
        IndexView.as_view(),
        name='runtests-index-testconfig'),
    url(r'^run/(?P<testmethod>\w+)/(?P<testpath>.+)/(?P<testconfig_pk>[0-9]+)',
        RunView.as_view(),
        name='runtests-run'),
    url(r'testconfig/add/$',
        TestConfigurationCreateView.as_view(),
        name='runtests-testconfig-add'),
    url(r'testconfig/(?P<pk>[0-9]+)/$',
        TestConfigurationUpdateView.as_view(),
        name='runtests-testconfig-update'),
    url(r'testconfig/(?P<pk>[0-9]+)/delete/$',
        TestConfigurationDeleteView.as_view(),
        name='runtests-testconfig-delete'),
]
