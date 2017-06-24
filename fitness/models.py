import math
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Activity(models.Model):
    name = models.CharField(max_length=128)
    time = models.DateTimeField()

    class Meta:
        ordering = ['-time']

    def points_with_heart_rate(self):
        return [a for a in self.stream() if a.get('heart_rate')]

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

    def points(self):
        return Point.objects.filter(lap__activity=self).order_by('time')

    def stream(self):
        return [a.as_dictionary() for a in self.points()]

    def track(self):
        return [
            (a['latitude'], a['longitude']) for a in self.stream()
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

    def total_distance(self, unit='km'):
        distance = self.stream()[-1]['distance']
        if unit == 'km':
            return distance / 1000.0
        return distance

    def total_time(self):
        return (self.stream()[-1]['time'] - self.stream()[0]['time']).total_seconds()

    def duration_as_string(self):
        total_seconds = int(self.total_time())
        total_minutes = int(total_seconds // 60)
        hours = int(total_minutes // 60)
        minutes = total_minutes - (60 * hours)
        seconds = total_seconds - (60 * total_minutes)
        if hours:
            return '{}:{:0>2}:{:0>2}'.format(hours, minutes, seconds)
        else:
            return '{}:{:0>2}'.format(minutes, seconds)

    def average_pace(self):
        seconds = self.total_time()
        distance = self.total_distance()
        if distance == 0:
            pace = 0
        else:
            pace = (seconds / 60.0) / distance
        return pace

    def average_pace_as_string(self):
        pace = self.average_pace()
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return '{}:{:0>2}'.format(minutes, seconds)

    def elevation_gain(self):
        gain = 0
        last_elevation = None
        points_up = 0
        for point in self.stream():
            if last_elevation is not None and point['altitude'] > last_elevation:
                if points_up < 2:
                    points_up += 1
                else:
                    gain += (int(point['altitude']) - int(last_elevation))
            else:
                points_up = 0
            last_elevation = point['altitude']
        return gain

    def has_heart_rate(self):
        return bool(self.points_with_heart_rate())

    @staticmethod
    def average(points, key):
        if isinstance(points[0][key], datetime.datetime):
            return points[0][key]
        return sum(p[key] for p in points) / len(points)

    def reduced_points(self):
        output_points = []
        current_points = []
        out_count = -1

        heart_rate_points = self.has_heart_rate()
        if heart_rate_points:
            input_points = self.points_with_heart_rate()
        else:
            input_points = self.points()

        unsampled_count = len(input_points)
        desired_points = 200
        factor = unsampled_count // desired_points

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


class Lap(models.Model):
    activity = models.ForeignKey(Activity, related_name='laps')
    lap = models.IntegerField()


class Point(models.Model):
    lap = models.ForeignKey(Lap, related_name='points')
    time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    heart_rate = models.FloatField(null=True)
    cadence = models.FloatField(null=True)
    distance = models.FloatField(default=0.0)
    speed = models.FloatField(default=0.0)

    def pace(self):
        return 1.0 / ((60.0 / 1000.0) * self.speed)

    def as_dictionary(self):
        return {
            'time': self.time,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'heart_rate': self.heart_rate,
            'cadence': self.cadence,
            'distance': self.distance,
            'speed': self.speed,
        }