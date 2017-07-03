# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-03 15:06
from __future__ import unicode_literals
import math
import dateutil

from django.db import migrations


def decompress(point):
    expanded = point.copy()
    expanded['time'] = dateutil.parser.parse(point['time'])
    return expanded


def point_stream(activity):
    return sorted([decompress(x) for x in activity.stream.values()], key=lambda h: h['time'])


def calculate_trimp(activity):
    trimp = 0
    last_point = None
    minimum = activity.owner.profile.minimum_heart_rate
    heart_range = activity.owner.profile.maximum_heart_rate - activity.owner.profile.minimum_heart_rate
    exponent = 1.92 if activity.owner.profile.gender == 'M' else 1.67
    points = [a for a in point_stream(activity) if a.get('heart_rate')]
    if not points:
        return 0
    for point in points:
        if last_point is not None:
            minutes = (point['time'] - last_point['time']).total_seconds() / 60.0
            average_heart_rate = (point['heart_rate'] + last_point['heart_rate']) / 2
            reserve = max((average_heart_rate - minimum) / heart_range, 0)
            trimp += (
                minutes * reserve * 0.64 * math.exp(exponent * reserve)
            )
        last_point = point
    return trimp


def reverse(apps, unused):
    pass


def create_profiles_for_existing_users(apps, unused):
    Activity = apps.get_model('fitness', 'Activity')
    for activity in Activity.objects.all():
        activity.trimp = int(calculate_trimp(activity))
        activity.save()


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0008_auto_20170702_2038'),
    ]
    operations = [
        migrations.RunPython(create_profiles_for_existing_users, reverse_code=reverse),
    ]