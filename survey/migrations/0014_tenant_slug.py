# Generated by Django 4.2.6 on 2023-12-17 17:59

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_employee_actual_zone_companyjson'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='slug',
            field=autoslug.fields.AutoSlugField(default=None, editable=False, populate_from='name'),
            preserve_default=False,
        ),
    ]
