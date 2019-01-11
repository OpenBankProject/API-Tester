# -*- coding: utf-8 -*-
"""
URLs for apitester
"""

from django.conf.urls import url, include

from base.views import HomeView

urlpatterns = [
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^obp/', include('obp.urls')),
    url(r'^runtests/', include('runtests.urls')),
]
