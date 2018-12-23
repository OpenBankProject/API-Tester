# -*- coding: utf-8 -*-
"""
Forms of runtests app
"""

from django import forms

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
                'placeholder': '3.1.0',
                'class': 'form-control',
            }
        ),
        required=False,
    )
    def __init__(self, *args, **kwargs):
        super(TestConfigurationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
