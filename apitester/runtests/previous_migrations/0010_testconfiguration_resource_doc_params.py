# Generated by Django 2.0.7 on 2020-09-14 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runtests', '0009_auto_20200911_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='testconfiguration',
            name='resource_doc_params',
            field=models.CharField(blank=True, help_text='Resource Doc Parameters to filter the APIs returned', max_length=255, null=True, verbose_name='Params'),
        ),
    ]
