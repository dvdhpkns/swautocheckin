# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
            preserve_default=True,
        ),
    ]
