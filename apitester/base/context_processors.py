# -*- coding: utf-8 -*-
"""
Context processors for base app
"""

from django.conf import settings
from django.contrib import messages

from obp.api import API, APIError


def api_root(request):
    """Returns the configured API_ROOT"""
    return {'API_ROOT': settings.API_ROOT}

def portal_page(request):
    """Returns the configured API_PORTAL"""
    if settings.API_PORTAL is None:
        return {'API_PORTAL': settings.API_HOST}
    else:
        return {'API_PORTAL': settings.API_PORTAL}

def api_username(request):
    """Returns the API username of the logged-in user"""
    username = 'not authenticated'
    if request.user.is_authenticated:
        try:
            api = API(request.session.get('obp'))
            data = api.get('/users/current')
            if 'username' in data:
                username = data['username']
        except APIError as err:
            messages.error(request, err)
    return {'API_USERNAME': username}


def logo_url(request):
    """Returns the configured LOGO_URL"""
    return {'logo_url': settings.LOGO_URL}


def override_css_url(request):
    """Returns the configured OVERRIDE_CSS_URL"""
    return {'override_css_url': settings.OVERRIDE_CSS_URL}

