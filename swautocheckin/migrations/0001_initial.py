# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Passenger',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confirmation_num', models.CharField(max_length=13)),
                ('flight_time', models.TimeField()),
                ('flight_date', models.DateField()),
                ('task_id', models.CharField(max_length=64)),
                ('boarding_group', models.CharField(max_length=3)),
                ('success', models.BooleanField(default=False)),
                ('passenger', models.ForeignKey(to='swautocheckin.Passenger')),
            ],
        ),
    ]
