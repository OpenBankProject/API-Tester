# -*- coding: utf-8 -*-
"""
Forms of runtests app
"""

from django import forms
import random
from .models import TestConfiguration

from django.core.validators import RegexValidator, ValidationError


class TestConfigurationForm(forms.ModelForm):
    class Meta:
        model = TestConfiguration
        exclude = ['owner']

    

    def clean_api_version(self):
        allowed_api_versions = ['OBPv4.0.0', 'OBPv3.1.0', 'OBPv3.0.0', 'MXOFv0.0.1', 'BGv1.3']


        data = self.cleaned_data['api_version']
        if data not in allowed_api_versions:
            raise ValidationError("The API Version needs to be one of {}".format(allowed_api_versions) )

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    api_version = forms.CharField(
        label='API Version',
        help_text='Version of the API to initially generate in the format STANDARDvVERSION e.g. OBPv4.1.0',
        #validators=[validate_api_standard],
        widget=forms.TextInput(
            attrs={
                'value': 'OBPv4.1.0',
                'placeholder': 'OBPv4.1.0',
                'class': 'form-control'
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
