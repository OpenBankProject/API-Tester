# -*- coding: utf-8 -*-
"""
Views of runtests app
"""

import json
import urllib
import re
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from obp.api import API, APIError
import logging
from .forms import TestConfigurationForm
from .models import TestConfiguration,ProfileOperation

LOGGER = logging.getLogger(__name__)
# TODO: These have to map to attributes of models.TestConfiguration
URLPATH_DEFAULT = [
    '3.1.0',
    'Test', 'Test', '1',
    '1', '1', '1', '1',
    '1',
    '1', '1', '1', '1',
    '1', '1', '1',
    '1', '1',
]

URLPATH_REPLACABLES = [
    'API_VERSION',
    'USERNAME', 'USER_ID', 'PROVIDER_ID',
    'BANK_ID', 'BRANCH_ID', 'ATM_ID', 'PRODUCT_CODE',
    'OTHER_ACCOUNT_ID',
    'ACCOUNT_ID', 'VIEW_ID', 'TRANSACTION_ID', 'COUNTERPARTY_ID',
    'CUSTOMER_ID', 'MEETING_ID', 'CONSUMER_ID',
    'FROM_CURRENCY_CODE', 'TO_CURRENCY_CODE',
]

class IndexView(LoginRequiredMixin, TemplateView):
    """Index view for runtests"""
    template_name = "runtests/index.html"

    def get_testconfigs(self, testconfig_pk):
        testconfigs = {
            'available': [],
            'selected': None,
        }
        testconfigs['available'] = TestConfiguration.objects.filter(
            owner=self.request.user).order_by('name')
        if testconfig_pk:
            try:
                testconfigs['selected'] = TestConfiguration.objects.get(
                    owner=self.request.user,
                    pk=testconfig_pk,
                )
            except TestConfiguration.DoesNotExist as err:
                raise PermissionDenied
        return testconfigs

    def get_post_or_update(self, method, testconfigs, testconfig_pk, path, data, swagger ):

        params = ''
        order = 100
        # Get saved profile operations
        try:
            objs = ProfileOperation.objects.filter(
                profile_id=testconfig_pk,
                operation_id=data[method]['operationId'],
                is_deleted=0
            )
        except ProfileOperation.DoesNotExist:
            objs = None

        request_body = {}
        urlpath = self.get_urlpath(testconfigs["selected"], path)
        if objs is not None and len(objs)>0:
            objs_list = []
            for obj in objs:
                params = obj.json_body
                order = obj.order
                urlpath = obj.urlpath
                replica_id = obj.replica_id
                remark = obj.remark if obj.remark is not None else data[method]['summary']
                objs_list.append({
                    'urlpath': urlpath,
                    'method': method,
                    'order': order,
                    'params': params,
                    'summary': remark,
                    'operationId': data[method]['operationId'],
                    'replica_id':replica_id,
                    'responseCode': 200,
                })
            return objs_list

        elif method == 'post' or method == 'put':
            # generate json body from swagger
            definition = data[method]['parameters'][0] if len(data[method]['parameters']) > 0 else None
            definition = definition['schema']['$ref'][14:]
            params = swagger['definitions'][definition]
            if len(params["required"]) > 0:
                for field in params["required"]:
                    # Match Profile variables
                    field_names = [ f.name for f in TestConfiguration._meta.fields]
                    if field in field_names:
                        request_body[field] = getattr(testconfigs["selected"], field)
                    else:
                        try:
                            request_body[field] = params["properties"][field].get("example", "")
                        except:
                            request_body[field] = None
            params = json.dumps(request_body, indent=4)

        return [{
            'urlpath': urlpath,
            'method': method,
            'order': order,
            'params': params,
            'summary': data[method]['summary'],
            'operationId': data[method]['operationId'],
            'replica_id':1,
            'responseCode': 200,
        }]

    def api_replace(self, string, match, value):
        """Helper to replace format strings from the API"""
        # API sometimes uses '{match}' or 'match' to denote variables
        return string. \
            replace('{{{}}}'.format(match), value). \
            replace(match, value)

    def get_urlpath(self, testconfig, path):
        """
        Gets a URL path
        where placeholders in given path are replaced by values from testconfig
        """
        urlpath = path
        for (index, match) in enumerate(URLPATH_REPLACABLES):
            value = getattr(testconfig, match.lower())
            if value:
                urlpath = self.api_replace(urlpath, match, value)
            else:
                urlpath = self.api_replace(urlpath, match, URLPATH_DEFAULT[index])

        return urlpath

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        calls = []
        testconfig_pk = kwargs.get('testconfig_pk', 0)
        testconfigs = self.get_testconfigs(testconfig_pk)
        api = API(self.request.session.get('obp'))

        if 'selected' in testconfigs and testconfigs['selected']:
            api_version = testconfigs['selected'].api_version

            if re.match("^[1-3]\.[0-9]\.[0-9]$", api_version) is None:
                api_version = settings.API_VERSION

            try:
                swagger = api.get_swagger(api_version)
            except APIError as err:
                messages.error(self.request, err)
            else:
                for path, data in swagger['paths'].items():
                    if 'get' in data:
                        call = self.get_post_or_update('get', testconfigs, testconfig_pk, path, data, swagger)
                        calls = calls+call
                    if 'post' in data:
                        call = self.get_post_or_update('post', testconfigs, testconfig_pk, path, data, swagger)
                        calls = calls + call

                    if 'put' in data:
                        call = self.get_post_or_update('put', testconfigs, testconfig_pk, path, data, swagger)
                        calls = calls + call

                    if 'delete' in data:
                        call = self.get_post_or_update('delete', testconfigs, testconfig_pk, path, data, swagger)
                        calls = calls + call

                calls = sorted(calls, key=lambda item: item['order'], reverse=False)

        context.update({
            'calls': calls,
            'testconfigs': testconfigs,
            'testconfig_pk': testconfig_pk,
        })

        return context


class RunView(LoginRequiredMixin, TemplateView):
    """Run an actual test against the API"""
    template_name = "runtests/index.html"

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(self.get_data(context), **response_kwargs)

    def get_data(self, context):
        # This should ensure everything in context is JSON-serialisable
        if 'view' in context:
            del context['view']
        return context

    def api_replace(self, string, match, value):
        """Helper to replace format strings from the API"""
        # API sometimes uses '{match}' or 'match' to denote variables
        return string.\
            replace('{{{}}}'.format(match), value).\
            replace(match, value)

    def get_urlpath(self, testconfig, path):
        """
        Gets a URL path
        where placeholders in given path are replaced by values from testconfig
        """
        urlpath = path
        for index, match in enumerate(URLPATH_REPLACABLES):
            value = getattr(testconfig, match.lower())
            if value:
                urlpath = self.api_replace(urlpath, match, value)
            else:
                urlpath = self.api_replace(urlpath, match, URLPATH_DEFAULT[index])
        return urlpath

    def get_config(self, testmethod, testpath, testconfig_pk, operation_id):
        """Gets test config from swagger and database"""
        urlpath = urllib.parse.unquote(testpath)

        status_code = 200

        if testmethod == 'post':
            status_code = 201
        elif testmethod == 'put':
            status_code = 200
        elif testmethod == 'delete':
            status_code = 204

        try:
            obj = ProfileOperation.objects.get(
                profile_id=testconfig_pk,
                operation_id=operation_id,
                is_deleted=0
            )
        except ProfileOperation.DoesNotExist:
            obj = None

        config = {
            'found': True,
            'method': testmethod,
            'status_code': status_code,
            'summary': 'Unknown',
            'urlpath': urlpath if obj is None else obj.urlpath,
            'operation_id': operation_id,
            'profile_id': testconfig_pk,
            'payload': self.request.POST.get('json_body'),
            'num_runs': self.request.POST.get('num_runs')
        }
        try:
            testconfig = TestConfiguration.objects.get(
                owner=self.request.user, pk=testconfig_pk)
        except TestConfiguration.DoesNotExist as err:
            raise PermissionDenied
        try:
            swagger = self.api.get_swagger(testconfig.api_version)
        except APIError as err:
            messages.error(self.request, err)
        else:
            for path, data in swagger['paths'].items():
                if testmethod in data and data[testmethod]['operationId'] == operation_id :
                    config.update({
                        'found': True,
                        'operation_id': data[testmethod]['operationId'],
                        'summary': data[testmethod]['summary'],
                        'urlpath': self.get_urlpath(testconfig, path),
                    })
        return config

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def run_test(self, config):
        """Runs a test with given config"""
        url = '{}{}'.format(settings.API_HOST, config['urlpath'])
        # Let APIError bubble up
        if config['method'] == 'get' or config['method'] == 'delete':
            response = self.api.call(config['method'], url)
        else:
            response = self.api.call(config['method'], url, json.loads(config['payload']))
        try:
            text = response.json()
        except json.decoder.JSONDecodeError as err:
            text = response.text
        text = json.dumps(
            text, sort_keys=True, indent=2, separators=(',', ': '))
        result = {
            'text': text,
            'execution_time': response.execution_time,
            'status_code': response.status_code,
        }
        return result

    def get_context_data(self, **kwargs):
        context = super(RunView, self).get_context_data(**kwargs)
        self.api = API(self.request.session.get('obp'))
        config = self.get_config(**kwargs)
        context.update({
            'config': config,
            'text': None,
            'execution_time': -1,
            'messages': [],
            'success': False,
        })

        if not config['found']:
            msg = 'Unknown path {}!'.format(kwargs['testpath'])
            context['messages'].append(msg)
            return context

        try:
            result = self.run_test(config)
        except APIError as err:
            context['messages'].append(err)
            return context
        else:
            context.update(result)

        # Test if status code is as expected
        if result['status_code'] != config['status_code']:
            msg = 'Status code is {}, but expected {}!'.format(
                result['status_code'], config['status_code'])
            context['messages'].append(msg)
            return context

        context['success'] = True
        return context


class TestConfigurationCreateView(LoginRequiredMixin, CreateView):
    model = TestConfiguration
    form_class = TestConfigurationForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TestConfigurationCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('runtests-index-testconfig', kwargs={
            'testconfig_pk': self.object.pk,
        })


class TestConfigurationUpdateView(LoginRequiredMixin, UpdateView):
    model = TestConfiguration
    form_class = TestConfigurationForm

    def get_object(self, **kwargs):
        object = super(TestConfigurationUpdateView, self).get_object(**kwargs)
        if self.request.user != object.owner:
            raise PermissionDenied
        return object


    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TestConfigurationUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('runtests-index-testconfig', kwargs={
            'testconfig_pk': self.object.pk,
        })


class TestConfigurationDeleteView(LoginRequiredMixin, DeleteView):
    model = TestConfiguration
    form_class = TestConfigurationForm
    success_url = reverse_lazy('runtests-index')

    def get_object(self, **kwargs):
        object = super(TestConfigurationDeleteView, self).get_object(**kwargs)
        if self.request.user != object.owner:
            raise PermissionDenied
        return object


def saveJsonBody(request):

    operation_id = request.POST.get('operation_id')
    json_body = request.POST.get('json_body', '')
    profile_id = request.POST.get('profile_id')
    order = request.POST.get('order')
    urlpath = request.POST.get('urlpath')
    replica_id = request.POST.get('replica_id')
    remark = request.POST.get('remark')

    #if not re.match("^{.*}$", json_body):
    #    json_body = "{{{}}}".format(json_body)

    data = {
        'operation_id' : operation_id,
        'json_body': json_body,
        'profile_id': profile_id,
        'order': order,
        'urlpath': urlpath,
        'remark':remark
    }

    profile_list = ProfileOperation.objects.update_or_create(
        operation_id=operation_id,
        profile_id=profile_id,
        replica_id=replica_id,
        defaults=data
    )

    return JsonResponse({'state': True})


def copyJsonBody(request):
    saveJsonBody(request)

    operation_id = request.POST.get('operation_id')
    json_body = request.POST.get('json_body', '')
    profile_id = request.POST.get('profile_id')
    order = request.POST.get('order')
    urlpath = request.POST.get('urlpath')
    remark = request.POST.get('remark')

    #if not re.match("^{.*}$", json_body):
    #    json_body = "{{{}}}".format(json_body)

    profile_list = ProfileOperation.objects.filter(
        operation_id=operation_id,
        profile_id=profile_id
    )

    replica_id = max([profile.replica_id for profile in profile_list])+1

    ProfileOperation.objects.create(profile_id = profile_id, operation_id = operation_id, json_body = json_body, order = order, urlpath = urlpath, remark=remark, replica_id = replica_id)

    return JsonResponse({'state': True})

def deleteJsonBody(request):
    saveJsonBody(request)

    operation_id = request.POST.get('operation_id')
    profile_id = request.POST.get('profile_id')
    replica_id = request.POST.get('replica_id')

    profile = ProfileOperation.objects.get(
        operation_id=operation_id,
        profile_id=profile_id,
        replica_id=replica_id
    )
    profile.is_deleted = 1
    profile.save()

    return JsonResponse({'state': True})
