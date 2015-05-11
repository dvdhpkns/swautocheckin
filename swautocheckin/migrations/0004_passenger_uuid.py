# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0003_reservation_rename_boarding_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='passenger',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
