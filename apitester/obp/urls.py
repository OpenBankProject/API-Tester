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

urlpatterns = [
    url(r'^oauth/initiate$',
        OAuthInitiateView.as_view(), name='obp-oauth-initiate'),
    url(r'^oauth/authorize$',
        OAuthAuthorizeView.as_view(), name='obp-oauth-authorize'),
    url(r'^directlogin$',
        DirectLoginView.as_view(), name='obp-directlogin'),
    url(r'^gatewaylogin$',
        GatewayLoginView.as_view(), name='obp-gatewaylogin'),
    url(r'^logout$',
        LogoutView.as_view(), name='obp-oauth-logout'),
]
