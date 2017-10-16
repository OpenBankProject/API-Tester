# -*- coding: utf-8 -*-
"""
Views of runtests app
"""

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView

from obp.api import API, APIError


class IndexView(LoginRequiredMixin, TemplateView):
    """Index view for runtests"""
    template_name = "runtests/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        api = API(self.request.session.get('obp'))
        swagger = api.get_swagger()
        calls = []
        for path, data in swagger['paths'].items():
            # Only GET requests for now
            if 'get' in data:
                call = {
                    'urlpath': path,
                    'method': 'get',
                    'summary': data['get']['summary'],
                    'responseCode': 200,
                }
                calls.append(call)

        context.update({
            'calls': calls,
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

    def get_config(self, test):
        test_method, test_path = test.split(' ')
        swagger = self.api.get_swagger()
        for path, data in swagger['paths'].items():
            if test_path == path and test_method in data:
                config = {
                    'urlpath': path,
                    'method': test_method,
                    'responseCode': 200,
                    'summary': data[test_method]['summary'],
                }
                return config
        return None

    def run_test(self, context):
        config = context['config']
        # Test if it runs
        try:
            response = self.api.call(config['method'], config['urlpath'])
            result = json.dumps(response.json(),
                sort_keys=True, indent=2, separators=(',', ': '))
            context.update({
                'result': result,
                'execution_time': response.execution_time,
            })
        except APIError as err:
            context['messages'].append(err)
            context['success'] = False
            return context

        # Test if status code is as expected
        if response.status_code != config['responseCode']:
            context['messages'].append('Wrong status code ({} != {})!'.format(
                config['responseCode'], response.status_code))
            context['success'] = False
            return context

        # Test if response includes certain string
        if 'responseHas' in config:
            data = response.json()
            if config['responseHas'] not in data:
                context['messages'].append('"{}" not in "{}"!'.format(
                    config['responseHas'], data))
                context['success'] = False
                return context
        return context

    def get_context_data(self, **kwargs):
        context = super(RunView, self).get_context_data(**kwargs)
        self.api = API(self.request.session.get('obp'))
        context.update({
            'config': self.get_config(kwargs['test']),
            'result': None,
            'execution_time': -1,
            'messages': [],
            'success': True,
        })
        if not context['config']:
            msg = 'Test {} is not configured!'.format(kwargs['test'])
            context['messages'].append(msg)
            context['success'] = False
            return context
        self.run_test(context)
        return context
