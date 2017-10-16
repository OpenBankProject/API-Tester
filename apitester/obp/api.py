# -*- coding: utf-8 -*-
"""
Module to handle the OBP API

It instantiates a convenience api object for imports, e.g.:
from obp.api import api
"""

from datetime import datetime
import logging
import time

from requests.exceptions import ConnectionError

from django.conf import settings
from django.contrib.auth import logout

from .directlogin import DirectLoginAuthenticator
from .gatewaylogin import GatewayLoginAuthenticator
from .oauth import OAuthAuthenticator


DATE_FORMAT = '%d/%b/%Y %H:%M:%S'
LOGGER = logging.getLogger(__name__)


def log(level, message):
    """Logs a given message on a given level to log facility"""
    now = datetime.now().strftime(DATE_FORMAT)
    msg = '[{}] API: {}'.format(now, message)
    LOGGER.log(level, msg)


class APIError(Exception):
    """Exception class for API errors"""
    pass


class API(object):
    """Implements an interface to the OBP API"""

    def __init__(self):
        self.set_base_path()

    def set_base_path(self, base_path=None):
        """Sets the basepath for API calls"""
        if base_path:
            self.base_path = settings.API_HOST + base_path
        else:
            self.base_path = settings.API_HOST + settings.API_BASE_PATH

    def get(self, request, urlpath=''):
        """Gets data from the API"""
        response = self.call(request, 'GET', urlpath)
        return self.handle_response(request, response)

    def delete(self, request, urlpath):
        """Deletes data from the API"""
        response = self.call(request, 'DELETE', urlpath)
        return self.handle_response(request, response)

    def post(self, request, urlpath, payload):
        """Posts data to the API"""
        response = self.call(request, 'POST', urlpath, payload)
        return self.handle_response(request, response)

    def put(self, request, urlpath, payload):
        """Puts data onto the API"""
        response = self.call(request, 'PUT', urlpath, payload)
        return self.handle_response(request, response)

    def get_swagger(self, request):
        """Gets the swagger definition from the API"""
        # TODO: Might be better with a proper caching backend
        if 'swagger' not in request.session:
            # FIXME: settings base path is a race condition!
            self.set_base_path(settings.API_SWAGGER_BASE_PATH)
            urlpath = '/resource-docs/v3.0.0/swagger'
            response = self.get(request, urlpath)
            # Set base path back
            self.set_base_path()
            request.session['swagger'] = response
            request.session.modified = True
            log(logging.INFO, 'Returning fresh swagger')
        else:
            log(logging.INFO, 'Returning cached swagger')
        return request.session['swagger']

    def handle_response_404(self, response, prefix):
        # Stripping HTML body ...
        if response.text.find('body'):
            msg = response.text.split('<body>')[1].split('</body>')[0]
        msg = '{} {}: {}'.format(
            prefix, response.status_code, msg)
        log(logging.ERROR, msg)
        raise APIError(msg)

    def handle_response_500(self, response, prefix):
        msg = '{} {}: {}'.format(
            prefix, response.status_code, response.text)
        log(logging.ERROR, msg)
        raise APIError(msg)

    def handle_response_error(self, request, prefix, error):
        if 'Invalid or expired access token' in error:
            logout(request)
        msg = '{} {}'.format(prefix, error)
        raise APIError(msg)

    def handle_response(self, request, response):
        """Handles the response, e.g. errors or conversion to JSON"""
        prefix = 'APIError'
        if response.status_code == 404:
            self.handle_response_404(response, prefix)
        elif response.status_code == 500:
            self.handle_response_500(response, prefix)
        elif response.status_code in [204]:
            return response.text
        else:
            data = response.json()
            if 'error' in data:
                self.handle_response_error(request, prefix, data['error'])
            return data

    def get_session(self, request):
        """
        Gets a session object to use for subsequent requests to the API
        TODO: Handle (de)serialization of Authenticator objects properly,
        to get rid of if/else
        """
        session = None
        if 'oauth' in request.session:
            kwargs = request.session.get('oauth').values()
            authenticator = OAuthAuthenticator(*kwargs)
        elif 'directlogin' in request.session:
            kwargs = request.session.get('directlogin').values()
            authenticator = DirectLoginAuthenticator(*kwargs)
        elif 'gatewaylogin' in request.session:
            kwargs = request.session.get('gatewaylogin').values()
            authenticator = GatewayLoginAuthenticator(*kwargs)
        else:
            raise APIError('No token found in session!')
        return authenticator.get_session()

    def clear_session(self, request):
        """
        Clear API-related session data in request
        TODO: Adapt accordingly once get_session has been improved
        """
        keys = ['oauth', 'directlogin', 'gatewaylogin', 'swagger']
        modified = False
        for key in keys:
            if key in request:
                del request.session[key]
                modified = True
        if modified:  # do not change 'modified' if not explicitly changed here
            request.session.modified = True

    def call(self, request, method='GET', urlpath='', payload=None):
        """Workhorse which actually calls the API"""
        url = self.base_path + urlpath
        log(logging.INFO, '{} {}'.format(method, url))
        if payload:
            log(logging.INFO, 'Payload: {}'.format(payload))
        if not hasattr(request, 'api'):
            request.api = self.get_session(request)
        time_start = time.time()
        try:
            if payload:
                response = request.api.request(method, url, json=payload)
            else:
                response = request.api.request(method, url)
        except ConnectionError as err:
            raise APIError(err)
        time_end = time.time()
        elapsed = int((time_end - time_start) * 1000)
        log(logging.INFO, 'Took {} ms'.format(elapsed))
        response.execution_time = elapsed
        return response


api = API()
