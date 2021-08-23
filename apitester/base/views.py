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
            'gatewaylogin_form': GatewayLoginForm(),
            'override_css_url': settings.OVERRIDE_CSS_URL,
            'logo_url': settings.LOGO_URL,
        })
        return context
