import math
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

import dateutil.parser


class Theme(models.Model):
    name = models.CharField(max_length=128)
    dark = models.BooleanField(default=True)

    def __str__(self):
        return self.name.title()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, theme=Theme.objects.first())


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Activity(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    time = models.DateTimeField()
    distance = models.FloatField(null=True)
    duration = models.FloatField(null=True)
    elevation = models.FloatField(null=True)
    data_points = models.IntegerField(null=True)
    stream = JSONField(encoder=DjangoJSONEncoder, null=True)

    class Meta:
        ordering = ['-time']

    def points_with_heart_rate(self):
        return [a for a in self.point_stream() if a.get('heart_rate')]

    def trimp(self, minimum, maximum, male=True):
        trimp = 0
        last_point = None
        heart_range = maximum - minimum
        exponent = 1.92 if male else 1.67
        points = self.points_with_heart_rate()
        if not points:
            return None
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

    @staticmethod
    def decompress(point):
        expanded = point.copy()
        expanded['time'] = dateutil.parser.parse(point['time'])
        return expanded

    def point_stream(self):
        return sorted([self.decompress(x) for x in self.stream.values()], key=lambda h: h['time'])

    def track(self):
        return [
            (a['latitude'], a['longitude']) for a in self.point_stream()
        ]

    def svg_points(self):
        track = self.track()
        max_latitude = max(a[0] for a in track)
        min_latitude = min(a[0] for a in track)
        latitude_range = max_latitude - min_latitude
        max_longitude = max(a[1] for a in track)
        min_longitude = min(a[1] for a in track)
        longitude_range = max_longitude - min_longitude
        return [
            (
                30 * (a[1] - min_longitude) / longitude_range,
                30 * (1 - (a[0] - min_latitude) / latitude_range),
            )
            for a in track
        ]

    def display_distance(self, unit='km'):
        if unit == 'km':
            return self.distance / 1000.0
        return self.distance

    def duration_as_string(self):
        total_seconds = int(self.duration)
        total_minutes = int(total_seconds // 60)
        hours = int(total_minutes // 60)
        minutes = total_minutes - (60 * hours)
        seconds = total_seconds - (60 * total_minutes)
        if hours:
            return '{}:{:0>2}:{:0>2}'.format(hours, minutes, seconds)
        else:
            return '{}:{:0>2}'.format(minutes, seconds)

    def average_pace(self):
        distance = self.display_distance()
        if distance == 0:
            pace = 0
        else:
            pace = (self.duration / 60.0) / distance
        return pace

    def average_pace_as_string(self):
        pace = self.average_pace()
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return '{}:{:0>2}'.format(minutes, seconds)

    def has_heart_rate(self):
        return bool(self.points_with_heart_rate())

    @staticmethod
    def average(points, key):
        if isinstance(points[0][key], datetime.datetime):
            return points[0][key]
        try:
            return (sum(p[key] or 0 for p in points) / len(points)) or None
        except:
            print(key, points)
            raise

    def reduced_points(self):
        output_points = []
        current_points = []
        out_count = -1

        input_points = self.point_stream()

        unsampled_count = len(input_points)
        desired_points = 200
        factor = max(unsampled_count // desired_points, 1)

        for index, point in enumerate(input_points):
            current_points.append(point)
            if index % factor == 0:
                out_count += 1
                keys = current_points[0].keys()
                new_point = {
                    k: self.average(current_points, k) for k in keys
                }
                output_points.append(new_point)
                current_points = []
        return output_points

    def geo_json(self):
        data = []
        points = self.reduced_points()
        for index, point in enumerate(points):
            if index > 0:
                geo_point = {
                    'type': 'Feature',
                    'properties': {
                        'id': index - 1,
                        'elevation': point.get('altitude'),
                        'speed': point.get('speed'),
                        'distance': point.get('distance'),
                        'cadence': point.get('cadence'),
                    },
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [
                                last_point.get('longitude'),
                                last_point.get('latitude'),
                            ],
                            [
                                point.get('longitude'),
                                point.get('latitude'),
                            ]
                        ]
                    }
                }
                if point.get('heart_rate') is not None:
                    geo_point['properties']['heart_rate'] = point.get('heart_rate')
                data.append(geo_point)
            last_point = point
        first = points[0]
        last = points[-1]
        data.append({
            "type": "Feature",
            "properties": {
                "id": "progress",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    first.get('longitude'), first.get('latitude')
                ]
            }
        })
        data.append({
            "type": "Feature",
            "properties": {
                "id": "start",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    first.get('longitude'), first.get('latitude')
                ]
            }
        })
        data.append({
            "type": "Feature",
            "properties": {
                "id": "stop",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    last.get('longitude'), last.get('latitude')
                ]
            }
        })
        return data