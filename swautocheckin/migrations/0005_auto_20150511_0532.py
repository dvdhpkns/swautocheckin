# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0004_passenger_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='success',
            field=models.NullBooleanField(default=None),
        ),
    ]
