# -*- coding: utf-8 -*-
"""
URLs for OBP app
"""

from django.conf.urls import url

from .views import (
    OAuthInitiateView, OAuthAuthorizeView,
    DirectLoginView,
    GatewayLoginView,
    LogoutView,
)

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

LogAtStart()

urlpatterns = [
    url(r'^oauth/initiate$',
        OAuthInitiateView.as_view(), name='oauth-initiate'),
    url(r'^oauth/authorize$',
        OAuthAuthorizeView.as_view(), name='oauth-authorize'),
    url(r'^directlogin$',
        DirectLoginView.as_view(), name='directlogin'),
    url(r'^gatewaylogin$',
        GatewayLoginView.as_view(), name='gatewaylogin'),
    url(r'^logout$',
        LogoutView.as_view(), name='oauth-logout'),
]
