# -*- coding: utf-8 -*-
"""
Forms of runtests app
"""

from django import forms

from .models import TestConfiguration


class TestConfigurationForm(forms.ModelForm):
    class Meta:
        model = TestConfiguration
        exclude = ['owner']

    def __init__(self, *args, **kwargs):
        super(TestConfigurationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
