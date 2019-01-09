# -*- coding: utf-8 -*-
"""
Forms of runtests app
"""

from django import forms
import random
from .models import TestConfiguration

from django.core.validators import RegexValidator


class TestConfigurationForm(forms.ModelForm):
    class Meta:
        model = TestConfiguration
        exclude = ['owner']

    api_version = forms.CharField(
        label='api_verison',
        validators=[RegexValidator(r'^\d\.\d\.\d$', 'Please Input correct api_version like 3.1.0')],
        widget=forms.TextInput(
            attrs={
                'value': '3.1.0',
                'placeholder': '3.1.0',
                'class': 'form-control',
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(TestConfigurationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'name':
                profile_key = int(random.random() * 10000000)
                field.widget.attrs['value'] = 'Profile{}'.format(profile_key)
                field.widget.attrs['placeholder'] = 'Profile{}'.format(profile_key)
            field.widget.attrs['class'] = 'form-control'
