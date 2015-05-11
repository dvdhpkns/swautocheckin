# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swautocheckin', '0002_reservation_uuid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservation',
            old_name='boarding_group',
            new_name='boarding_position'
        ),
    ]
