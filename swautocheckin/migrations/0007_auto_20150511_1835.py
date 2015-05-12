# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0006_reservation_child_reservations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='boarding_position',
            field=models.CharField(max_length=3, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='task_id',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
    ]
