# -*- coding: utf-8 -*-
"""
Views for base app
"""

from django.conf import settings
from django.views.generic import TemplateView

from obp.forms import DirectLoginForm, GatewayLoginForm


class HomeView(TemplateView):
    """View for home page"""
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({
            'API_HOST': settings.API_HOST,
            'directlogin_form': DirectLoginForm(),
            'ALLOW_DIRECT_LOGIN':settings.ALLOW_DIRECT_LOGIN,
            'gatewaylogin_form': GatewayLoginForm(),
            'ALLOW_GATEWAY_LOGIN': settings.ALLOW_GATEWAY_LOGIN,
            'override_css_url': settings.OVERRIDE_CSS_URL,
            'logo_url': settings.LOGO_URL,
            "explorer_url":f'{settings.API_EXPLORER_HOST}?version=OBPv{settings.API_VERSION}&operation_id=OBPv1_4_0-getResourceDocsObp&currentTag=Documentation&locale=en_GB#OBPv1_4_0-getResourceDocsObp',
        })
        return context
