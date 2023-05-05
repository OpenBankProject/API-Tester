# -*- coding: utf-8 -*-
"""
Views for base app
"""

from django.conf import settings
from django.views.generic import TemplateView

from obp.forms import DirectLoginForm, GatewayLoginForm
from obp.api import API, APIError

def get_api_versions(request):
    api = API(request.session.get('obp'))
    try:
        urlpath = '/api/versions'
        result = api.get(urlpath)
        print("result from view.py", result)
        if 'scanned_api_versions' in result:
            return [apiversion['API_VERSION'] for apiversion in sorted(result['scanned_api_versions'], key=lambda d: d['API_VERSION'])]
        else:
            return []
    except APIError as err:
        messages.error(self.request, err)
        return []
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
        })
        return context
