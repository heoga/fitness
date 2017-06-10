import math

from django.db import models


class Activity(models.Model):
    name = models.CharField(max_length=128)
    time = models.DateTimeField()

    def trimp(self, minimum, maximum, male=True):
        trimp = 0
        last_point = None
        heart_range = maximum - minimum
        exponent = 1.92 if male else 1.67
        for lap in self.lap_set.all().order_by('lap'):
            for point in lap.point_set.all().order_by('time'):
                if last_point is not None:
                    minutes = (point.time - last_point.time).total_seconds() / 60.0
                    average_heart_rate = (point.heart_rate + last_point.heart_rate) / 2
                    reserve = max((average_heart_rate - minimum) / heart_range, 0)
                    trimp += (
                        minutes * reserve * 0.64 * math.exp(exponent * reserve)
                    )
                last_point = point
        return trimp


class Lap(models.Model):
    activity = models.ForeignKey(Activity)
    lap = models.IntegerField()


class Point(models.Model):
    lap = models.ForeignKey(Lap)
    time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    heart_rate = models.FloatField()
    cadence = models.FloatField()
