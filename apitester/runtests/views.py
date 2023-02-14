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
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from obp.api import API, APIError
import logging
from .forms import TestConfigurationForm
from .models import TestConfiguration, ProfileOperation



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

    def get_post_or_update(self, method, testconfigs, testconfig_pk, path, data, swagger):
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
        urlpath = get_urlpath(testconfigs["selected"], path)

        if objs is not None and len(objs) > 0:
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
                    'replica_id': replica_id,
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
                    field_names = [f.name for f in TestConfiguration._meta.fields]
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
            'replica_id': 1,
            'responseCode': 200,
        }]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        calls = []
        testconfig_pk = kwargs.get('testconfig_pk', 0)
        testconfigs = self.get_testconfigs(testconfig_pk)

        swaggers = ProfileOperation.objects.filter(profile_id=int(testconfig_pk)).order_by('-save_time', 'id')

        operation_ids = []
        for operation in swaggers:
            if operation.is_deleted==0:
                obj = {
                    'id': operation.id,
                    'urlpath': get_urlpath(testconfigs['selected'], operation.urlpath),
                    'method': operation.method,
                    'order': operation.order,
                    'params': operation.json_body,
                    'summary': operation.remark,
                    'operationId': operation.operation_id,
                    'replica_id': operation.replica_id,
                    'responseCode': 200,
                }
                calls.append(obj)
            if operation.operation_id not in operation_ids:
                operation_ids.append(operation.operation_id)

        context.update({
            'swaggers': operation_ids,
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
        return string. \
            replace('{{{}}}'.format(match), value). \
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

    # get config for one operation.
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
            # get profile from the database..
            objs = ProfileOperation.objects.filter(
                profile_id=int(testconfig_pk),  # 1
                operation_id=operation_id,  # OBPv3.0.0-getBanks
                is_deleted=0
            )
        except ProfileOperation.DoesNotExist:
            objs = None

        config = {
            'found': True,
            'method': testmethod,
            'status_code': status_code,
            'summary': 'Unknown',
            'urlpath': urlpath if objs is None or len(objs) == 0 else objs[0].urlpath,
            'operation_id': operation_id,
            'profile_id': testconfig_pk,
            'payload': self.request.POST.get('json_body')
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
            for path, data in swagger['path'].items():
                print("path is ", path)
                if testmethod in data and data[testmethod]['operationId'] == operation_id:
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
            try:
                response = self.api.call(config['method'], url, json.loads(config['payload']))
            except:
                response = self.api.call(config['method'], url)
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
        payload = self.request.POST.get('json_body')
        config = self.get_config(**kwargs)

        if context['testpath'] is not None:
            config.update({'urlpath': context['testpath']})
        if payload is not None:
            config.update({'payload': payload})
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

    def get_success_url(self):
        testconfig = self.get_testconfigs(self.object.pk)['selected']
        self.api = API(self.request.session.get('obp'))
        
        api_version = testconfig.api_version
        resource_doc_params = testconfig.resource_doc_params

        #print ("api_version is {}".format(api_version))
        #print ("resource_doc_params is {}".format(resource_doc_params))
        
        swagger = self.api.get_swagger(api_version, resource_doc_params)

        #print("the swagger is {}".format(swagger))


        # Within successful response we expect there to be path
        try:
            swagger_path_items = swagger['path'].items()
        except KeyError as err:
            # We probably can extract the reason from the response("swagger")
            response_code = swagger['code']
            message = swagger['message']
            # TODO Return this information calmly rather than as an exception.
            raise Exception(str(response_code) + " " + str(message))

            #return JsonResponse({'code': str(response_code), 'message': str(message)}, safe=True)
            #return reverse('runtests-index-testconfig', kwargs={})

        # Continue extracting the endpoints from the swagger json
        for path, data in swagger_path_items:
            try: # there are some special endpoints in obp-api side, the swagger format is not good enough to show in the API Tester, here we just log them.
                for method, content in data.items():
                    urlpath = path
                    remark = content['summary']
                    params = ''
                    if method == 'post' or method == 'put':
                        definition = content['parameters'][0] if len(content['parameters']) > 0 else None
                        definition = definition['schema']['$ref'][14:]  # /definitions/BankJson400 -->  BankJson400
                        params = swagger['definitions'][definition]
                        request_body = {}
                        if len(params["required"]) > 0:
                            for field in params["required"]:
                                # Match Profile variables
                                field_names = [f.name for f in TestConfiguration._meta.fields]
                                if field in field_names:
                                    request_body[field] = getattr(testconfig, field)
                                else:
                                    try:
                                        request_body[field] = params["properties"][field].get("example", "")
                                    except:
                                        request_body[field] = None
                        params = json.dumps(request_body, indent=4)
                    operation_id = content['operationId']
                    profile_id = testconfig.pk
                    profileOperation_insert(operation_id, params, profile_id, urlpath, remark, method)
            except Exception as e:
                #TODO, maybe later, we can show this to the HTML.
                logging.error("this endpoint (path = {}) can not be used in API_Tester, check the format.".format(str(path)))
                logging.error("the reason is : {}".format(e)) 

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

def profileOperation_insert(operation_id, json_body, profile_id, urlpath, remark, method, replica_id = 1, order=100):
    data = {
        'operation_id': operation_id,
        'json_body': json_body,
        'profile_id': profile_id,
        'order': order,
        'urlpath': urlpath,
        'remark': remark,
        'is_deleted': 0,
        'method': method,
        'save_time': str(int(time.time()))
    }

    ProfileOperation.objects.update_or_create(
        operation_id=operation_id,
        profile_id=profile_id,
        replica_id=replica_id,
        defaults=data
    )

def saveJsonBody(request):
    operation_id = request.POST.get('operation_id')
    json_body = request.POST.get('json_body', '')
    profile_id = request.POST.get('profile_id')
    order = request.POST.get('order')
    urlpath = request.POST.get('urlpath')
    replica_id = request.POST.get('replica_id')
    method = request.POST.get('method')
    remark = request.POST.get('remark')

    profileOperation_insert(operation_id, json_body, profile_id, urlpath, remark, method, replica_id, order)

    return JsonResponse({'state': True})


def copyJsonBody(request):
    operation_id = request.POST.get('operation_id')
    json_body = request.POST.get('json_body', '')
    profile_id = request.POST.get('profile_id')
    order = request.POST.get('order')
    urlpath = request.POST.get('urlpath')
    remark = request.POST.get('remark')
    method = request.POST.get('method')

    profile_list = ProfileOperation.objects.filter(
        operation_id=operation_id,
        profile_id=profile_id
    )

    replica_id = max([profile.replica_id for profile in profile_list]) + 1

    profileOperation_insert(operation_id, json_body, profile_id, urlpath, remark, method, replica_id, order)

    return JsonResponse({'state': True})

def deleteJsonBody(request):
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

def api_replace(string, match, value):
    """Helper to replace format strings from the API"""
    # API sometimes uses '{match}' or 'match' to denote variables
    return string. \
        replace('{{{}}}'.format(match), value). \
        replace(match, value)

def get_urlpath(testconfig, path):
    """
    Gets a URL path
    where placeholders in given path are replaced by values from testconfig
    """
    urlpath = path
    for (index, match) in enumerate(URLPATH_REPLACABLES):
        if match in urlpath:
            value = getattr(testconfig, match.lower())
            if value:
                urlpath = api_replace(urlpath, match, value)
            else:
                urlpath = api_replace(urlpath, match, URLPATH_DEFAULT[index])

    return urlpath

def addAPI(request):
    operation_id = request.POST.get('operation_id')  # get the operation_id
    profile_id = request.POST.get('profile_id')  # get the profile_id

    api = API(request.session.get('obp'))

    config = TestConfiguration.objects.get(
        id = profile_id
    )

    swagger = api.get_swagger(config.api_version)['path']
    print("swagger is:", swagger)
    params = ''
    urlpath=''
    remark=''

    method_total = ''
    for path,operation in swagger.items():
        for method, content in operation.items():
            if content['operationId']==operation_id:
                urlpath = path
                remark = content['summary']
                method_total = method
                if method == 'post' or method == 'put':
                    definition = content['parameters'][0] if len(content['parameters']) > 0 else None
                    definition = definition['schema']['$ref'][14:]
                    params = swagger['definitions'][definition]
                    request_body = {}
                    if len(params["required"]) > 0:
                        for field in params["required"]:
                            # Match Profile variables
                            field_names = [f.name for f in TestConfiguration._meta.fields]
                            if field in field_names:
                                request_body[field] = getattr(config, field)
                            else:
                                try:
                                    request_body[field] = params["properties"][field].get("example", "")
                                except:
                                    request_body[field] = None
                    params = json.dumps(request_body, indent=4)
                break

    profile_list = ProfileOperation.objects.filter(
        operation_id=operation_id,
        profile_id=profile_id
    )
    replica_id = 1
    # if the relica_id is existing, then
    if len(profile_list) > 0:
        replica_id = max([profile.replica_id for profile in profile_list]) + 1

    ProfileOperation.objects.create(  # create the new operation.
        profile_id=profile_id,
        operation_id=operation_id,
        json_body=params,
        order=100,
        urlpath=urlpath,
        remark=remark,
        replica_id=replica_id,
        is_deleted=0,
        method=method_total,
        save_time=int(time.time())
    )

    return JsonResponse({
        'state': True,
        'profile_id': profile_id,
        'operation_id': operation_id,
        'json_body': params,
        'order': 100,
        'urlpath': urlpath,
        'remark': remark,
        'replica_id': replica_id,
        'is_deleted': 0
    })