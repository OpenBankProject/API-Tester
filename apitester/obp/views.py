# -*- coding: utf-8 -*-
"""
Views for OBP app
"""


import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.urls import reverse, reverse
from django.views.generic import RedirectView, FormView

from requests_oauthlib import OAuth1Session
from requests_oauthlib.oauth1_session import TokenRequestDenied

from .api import api
from .authenticator import AuthenticatorError
from .forms import DirectLoginForm, GatewayLoginForm
from .oauth import OAuthAuthenticator


class OAuthInitiateView(RedirectView):
    """View to initiate OAuth session"""

    def get_callback_uri(self, request):
        """
        Gets the callback URI to where the user shall be returned after
        initiation at OAuth server
        """
        base_url = '{}://{}'.format(
            request.scheme, request.environ['HTTP_HOST'])
        uri = base_url + reverse('oauth-authorize')
        if 'next' in request.GET:
            uri = '{}?next={}'.format(uri, request.GET['next'])
        return uri

    def get_redirect_url(self, *args, **kwargs):
        callback_uri = self.get_callback_uri(self.request)
        try:
            authenticator = OAuthAuthenticator()
            authorization_url = authenticator.get_authorization_url(callback_uri)
        except AuthenticatorError as err:
            messages.error(self.request, err)
            return reverse('home')
        else:
            self.request.session['oauth'] = {
                'token': authenticator.token,
                'secret': authenticator.secret,
            }
            self.request.session.modified = True
            return authorization_url


class OAuthAuthorizeView(RedirectView):
    """View to authorize user after OAuth 1 initiation"""

    def get_redirect_url(self, *args, **kwargs):
        kwargs = self.request.session.get('oauth').values()
        authenticator = OAuthAuthenticator(*kwargs)
        authorization_url = self.request.build_absolute_uri()
        try:
            authenticator.update_token(authorization_url)
        except AuthenticatorError as err:
            messages.error(self.request, err)
        else:
            self.request.session['oauth'] = {
                'token': authenticator.token,
                'secret': authenticator.secret,
            }
            self.request.session.modified = True
            authenticator.login_to_django(self.request)
            messages.success(self.request, 'OAuth login successful!');
        redirect_url = self.request.GET.get('next', reverse('runtests-index'))
        return redirect_url


class DirectLoginView(FormView):
    """View to login via DirectLogin"""
    form_class = DirectLoginForm
    template_name = 'obp/directlogin.html'

    def get_success_url(self):
        messages.success(self.request, 'DirectLogin successful!');
        return reverse('runtests-index')

    def form_valid(self, form):
        """
        Stores a DirectLogin token in the request's session for use in
        future requests. It also logs in to Django.
        """
        authenticator = form.cleaned_data['authenticator']
        # TODO: Find a better way to handle serialization
        self.request.session['directlogin'] = {
            'token': authenticator.token,
        }
        self.request.session.modified = True
        authenticator.login_to_django(self.request)
        return super(DirectLoginView, self).form_valid(form)


class GatewayLoginView(FormView):
    """View to login via GatewayLogin"""
    form_class = GatewayLoginForm
    template_name = 'obp/gatewaylogin.html'

    def get_success_url(self):
        messages.success(self.request, 'GatewayLogin successful!');
        return reverse('runtests-index')

    def form_valid(self, form):
        """
        Stores a GatewayLogin token in the request's session for use in
        future requests. It also logs in to Django.
        """
        authenticator = form.cleaned_data['authenticator']
        # TODO: Find a better way to handle serialization
        self.request.session['gatewaylogin'] = {
            'token': authenticator.token,
        }
        self.request.session.modified = True
        authenticator.login_to_django(self.request)
        return super(GatewayLoginView, self).form_valid(form)


class LogoutView(RedirectView):
    """View to logout"""

    def get_redirect_url(self, *args, **kwargs):
        logout(self.request)
        try:
            del self.request.session['oauth']
            del self.request.session['directlogin']
            del self.request.session['gatewaylogin']
        except KeyError:
            pass
        self.request.session.modified = True
        return reverse('home')
