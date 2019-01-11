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

urlpatterns = []
