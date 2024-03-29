# -*- coding: utf-8 -*-
"""
Module to handle the OBP API

It instantiates a convenience api object for imports, e.g.:
from obp.api import api
"""

from datetime import datetime
import importlib
import logging
import time

import requests
from requests.exceptions import ConnectionError

from django.conf import settings
from django.core.cache import cache


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
    session = None
    swagger = None

    def __init__(self, session_data=None):
        if session_data:
            self.start_session(session_data)
        self.session_data = session_data

    def call(self, method='GET', url='', payload=None):
        """Workhorse which actually calls the API"""
        log(logging.INFO, '{} {}'.format(method, url))
        if payload:
            log(logging.INFO, 'Payload: {}'.format(payload))
        # use `requests` if no session has been started
        session = self.session or requests
        time_start = time.time()
        try:
            if payload:
                response = session.request(method, url, json=payload, verify=False)
            else:
                response = session.request(method, url, verify=False)
        except ConnectionError as err:
            raise APIError(err)
        time_end = time.time()
        elapsed = int((time_end - time_start) * 1000)
        log(logging.INFO, 'Took {} ms'.format(elapsed))
        response.execution_time = elapsed
        return response

    def get(self, urlpath=''):
        """
        Gets data from the API

        Convenience call which uses API_ROOT from settings
        """
        url = settings.API_ROOT + urlpath
        response = self.call('GET', url)
        return self.handle_response(response)

    def delete(self, urlpath):
        """
        Deletes data from the API

        Convenience call which uses API_ROOT from settings
        """
        url = settings.API_ROOT + urlpath
        response = self.call('DELETE', url)
        return self.handle_response(response)

    def post(self, urlpath, payload):
        """
        Posts data to given urlpath with given payload

        Convenience call which uses API_ROOT from settings
        """
        url = settings.API_ROOT + urlpath
        response = self.call('POST', url, payload)
        return self.handle_response(response)

    def put(self, urlpath, payload):
        """
        Puts data on given urlpath with given payload

        Convenience call which uses API_ROOT from settings
        """
        url = settings.API_ROOT + urlpath
        response = self.call('PUT', url, payload)
        return self.handle_response(response)

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

    def handle_response_error(self, prefix, error):
        if 'Invalid or expired access token' in error:
            raise APIError(error)
        msg = '{} {}'.format(prefix, error)
        raise APIError(msg)

    def handle_response(self, response):
        """Handles the response, e.g. errors or conversion to JSON"""
        prefix = 'APIError'
        if response.status_code == 404:
            self.handle_response_404(response, prefix)
        elif response.status_code == 500:
            self.handle_response_500(response, prefix)
        elif response.status_code in [204]:
            return response.text
        else:
            try:
                data = response.json()
            except:
                data = ""
            if 'error' in data:
                self.handle_response_error(prefix, data['error'])
            return data

    def start_session(self, session_data):
        """
        Starts a session with given session_data:
        - Authenticator class name (e.g. obp.oauth.OAuthAuthenticator)
        - Token data
        for subsequent requests to the API
        """
        if 'authenticator' in session_data and\
                'authenticator_kwargs' in session_data:
            mod_name, cls_name = session_data['authenticator'].rsplit('.', 1)
            log(logging.INFO, 'Authenticator {}'.format(cls_name))
            cls = getattr(importlib.import_module(mod_name), cls_name)
            authenticator = cls(**session_data['authenticator_kwargs'])
            self.session = authenticator.get_session()
            return self.session
        else:
            return None

    def get_swagger(self, api_version='OBPv3.1.0', resource_doc_params=''):
        """
        Gets the swagger definition from the API
        Uses API version 3.0.0 per default, but can be overridden by e.g.
        testconfig
        """
        """
        Typical path
        https://apisandbox.openbankproject.com/obp/v3.1.0/resource-docs/v3.1.0/swagger?functions=getBanks,bankById


        https://apisandbox.ofpilot.com/mx-open-finance/v0.0.1/accounts

        """


        #
        # api_version MUST be specified in the following format: <STANDARD>v<VERSION>
        #
        # UKv2.0  /obp/v4.0.0/resource-docs/UKv2.0/obp (previously /obp/v4.0.0/resource-docs/v2.0/obp)
        # BGv1  /obp/v4.0.0/resource-docs/BGv1/obp (previously /obp/v4.0.0/resource-docs/v1/obp)
        # BGv1.3  /obp/v4.0.0/resource-docs/BGv1.3/obp (previously /obp/v4.0.0/resource-docs/v1.3/obp)
        # MXOFv0.0.1  /obp/v4.0.0/resource-docs/MXOFv0.0.1/obp
        # OBPv4.0.0  /obp/v4.0.0/resource-docs/OBPv4.0.0/obp (previously /obp/v4.0.0/resource-docs/v4.0.0/obp)
        # etc.

        urlpath = '/resource-docs/{}/swagger?{}'.format(api_version, resource_doc_params)

        print ("urlpath is {}".format(urlpath))

        if not cache.get(urlpath):
            swagger = self.get(urlpath)
            cache.set(urlpath, swagger, settings.CACHE_TIMEOUT)
        return cache.get(urlpath)

    def get_api_version_choices(self):
        """Gets a list of APIs Version and APIs Version as used by form choices"""
        choices = [('', ('Choose ...'))]
        result = self.get('/api/versions')
        for version in sorted(result['scanned_api_versions'], key=lambda d: d['API_VERSION']) :
            choices.append((version['API_VERSION'], version['API_VERSION']))
        return choices
