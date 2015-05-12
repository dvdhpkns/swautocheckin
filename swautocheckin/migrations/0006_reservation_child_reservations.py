# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0005_auto_20150511_0532'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='child_reservations',
            field=models.ManyToManyField(default=None, to='swautocheckin.Reservation', blank=True),
        ),
    ]
