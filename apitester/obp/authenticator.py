# -*- coding: utf-8 -*-
"""
Base authenticator for OBP app
"""

import hashlib

from django.contrib.auth import login
from django.contrib.auth.models import User


class AuthenticatorError(Exception):
    """Exception class for Authenticator errors"""
    pass


class Authenticator(object):
    """Authenticator to the API"""

    def login_to_django(self, request):
        """
        Logs the user into Django
        Kind of faking it to establish if a user is authenticated later on
        """
        from .api import api  # avoid cyclic import issue
        data = api.get(request, '/users/current')
        userid = data['user_id'] or data['email']
        username = hashlib.sha256(userid.encode('utf-8')).hexdigest()
        password = username
        user, _ = User.objects.get_or_create(
            username=username, password=password,
        )
        login(request, user)
