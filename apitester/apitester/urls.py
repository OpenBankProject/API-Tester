# -*- coding: utf-8 -*-
"""
URLs for apitester
"""

from django.conf.urls import url, include

from base.views import HomeView
from django.conf import settings
import logging

LOGGER = logging.getLogger(__name__)

def LogAtStart():
    LOGGER.log(logging.INFO, 'OAUTH_BASE_URL: {}'.format(
        settings.OAUTH_BASE_URL))

    LOGGER.log(logging.INFO, 'API_HOST: {}'.format(
        settings.API_HOST))

    LOGGER.log(logging.INFO, 'API_ROOT: {}'.format(
        settings.API_ROOT))
    print('OAUTH_BASE_URL: {}'.format(settings.OAUTH_BASE_URL))
    print('API_HOST: {}'.format(settings.API_HOST))
    print('API_ROOT: {}'.format(settings.API_ROOT))

LogAtStart()

urlpatterns = [
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^obp/', include('obp.urls')),
    url(r'^runtests/', include('runtests.urls')),
]
