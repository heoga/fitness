import math

from django.db import models


class Activity(models.Model):
    name = models.CharField(max_length=128)
    time = models.DateTimeField()

    class Meta:
        ordering = ['-time']

    def points_with_heart_rate(self):
        return Point.objects.filter(heart_rate__isnull=False,lap__activity=self).order_by('time')

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
                minutes = (point.time - last_point.time).total_seconds() / 60.0
                average_heart_rate = (point.heart_rate + last_point.heart_rate) / 2
                reserve = max((average_heart_rate - minimum) / heart_range, 0)
                trimp += (
                    minutes * reserve * 0.64 * math.exp(exponent * reserve)
                )
            last_point = point
        return trimp

    def points(self):
        return Point.objects.filter(lap__activity=self).order_by('time')

    def track(self):
        return [
            (a.latitude, a.longitude) for a in self.points()
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
        distance = self.points().last().distance
        if unit == 'km':
            return distance / 1000.0
        return distance

    def total_time(self):
        return (self.points().last().time - self.points().first().time).total_seconds()

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
