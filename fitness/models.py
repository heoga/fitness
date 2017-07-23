import math
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

from timezonefinder import TimezoneFinder
from pytz import timezone
import dateutil.parser

TIMEZONE_FINDER = TimezoneFinder()


def average(*args):
    return sum(args) / len(args)


def date_array(start, end):
    return [
        (start + datetime.timedelta(days=i)) for i in range(0, (end - start).days + 1)
    ]


def delta_minutes(new, old):
    return (new - old).total_seconds() / 60.0


def heart_rate_reserve(average_heart_rate, minimum_heart_rate, heart_reserve):
    return min(max((average_heart_rate - minimum_heart_rate) / heart_reserve, 0), 1)


def height_coordinate(value, average_value, max_range, height):
    return (height * (1 - (value - average_value) / max_range)) - (height / 2)


def range_and_average(iterable):
    max_value = max(iterable)
    min_value = min(iterable)
    range_value = max_value - min_value
    return range_value, average(max_value, min_value)


def width_coordinate(value, average_value, max_range, width):
    return (width * (value - average_value) / max_range) + (width / 2)


class Theme(models.Model):
    name = models.CharField(max_length=128)
    dark = models.BooleanField(default=True)

    def __str__(self):
        return self.name.title()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme)
    minimum_heart_rate = models.IntegerField(default=60)
    maximum_heart_rate = models.IntegerField(default=190)

    MALE = 'M'
    FEMALE = 'F'
    GENDER_CHOICES = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default=MALE,
    )

    def heart_rate_reserve(self):
        return self.maximum_heart_rate - self.minimum_heart_rate

    def percent_of_heart_rate_reserve(self, heart_rate):
        return max((heart_rate - self.minimum_heart_rate) / self.heart_rate_reserve(), 0)

    def save(self, *args, **kwargs):
        self.minimum_heart_rate = max(1, self.minimum_heart_rate)
        self.maximum_heart_rate = max(self.maximum_heart_rate, self.minimum_heart_rate + 1)
        super(Profile, self).save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):  # pragma: no cover
    if created:
        Profile.objects.create(user=instance, theme=Theme.objects.first())


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):  # pragma: no cover
    instance.profile.save()


class Activity(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    time = models.DateTimeField()
    distance = models.FloatField(null=True)
    duration = models.FloatField(null=True)
    elevation = models.FloatField(null=True)
    trimp = models.IntegerField(null=True)
    data_points = models.IntegerField(null=True)
    stream = JSONField(encoder=DjangoJSONEncoder, null=True)

    class Meta:
        ordering = ['-time']

    def local_time(self):
        for first_point in self.stream.values():
            timezone_name = TIMEZONE_FINDER.timezone_at(lng=first_point['longitude'], lat=first_point['latitude'])
            if timezone_name is None:
                local_zone = timezone('UTC')
            else:
                local_zone = timezone(timezone_name)
            return local_zone.normalize(self.time.astimezone(local_zone)).strftime('%d %B %Y at %H:%M')

    def points_with_heart_rate(self):
        return [a for a in self.point_stream() if a.get('heart_rate')]

    def delta_trimp(self, current_time, last_time, current_heart_rate, last_heart_rate):
        exponent = 1.92 if self.owner.profile.gender == 'M' else 1.67
        minutes = delta_minutes(current_time, last_time)
        average_heart_rate = average(current_heart_rate, last_heart_rate)
        reserve = self.owner.profile.percent_of_heart_rate_reserve(average_heart_rate)
        return (
            minutes * reserve * 0.64 * math.exp(exponent * reserve)
        )

    def calculate_trimp(self):
        trimp = 0
        last_point = None
        for point in self.points_with_heart_rate():
            if last_point is not None:
                trimp += self.delta_trimp(
                    point['time'], last_point['time'], point['heart_rate'], last_point['heart_rate']
                )
            last_point = point
        return trimp or None

    @staticmethod
    def decompress(point):
        if isinstance(point['time'], datetime.datetime):
            return point
        expanded = point.copy()
        expanded['time'] = dateutil.parser.parse(point['time'])
        return expanded

    def point_stream(self):
        return sorted([self.decompress(x) for x in self.stream.values()], key=lambda h: h['time'])

    def track(self):
        return [
            (a['latitude'], a['longitude']) for a in self.point_stream()
        ]

    def adjusted_track(self):
        track = self.track()
        max_latitude = max(a[0] for a in track)
        longitude_factor = math.cos(math.radians(max_latitude))
        return [(a[0], a[1] * longitude_factor) for a in track]

    def svg_points(self, width=30, height=30):
        track = self.adjusted_track()
        latitude_range, average_latitude = range_and_average([a[0] for a in track])
        longitude_range, average_longitude = range_and_average([a[1] for a in track])
        max_range = max([longitude_range, latitude_range])
        return [
            (
                width_coordinate(a[1], average_longitude, max_range, width),
                height_coordinate(a[0], average_latitude, max_range, height),
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
        if isinstance(points[0].get(key), datetime.datetime):
            return points[0][key]
        return (sum(p.get(key) or 0 for p in points) / len(points)) or None

    @classmethod
    def condense_points(cls, points):
        keys = points[0].keys()
        return {
            k: cls.average(points, k) for k in keys
        }

    @staticmethod
    def reduction_factor(points):
        return max(len(points) // 200, 1)

    def reduced_points(self):
        output_points = []
        current_points = []
        input_points = self.point_stream()
        factor = self.reduction_factor(input_points)
        for index, point in enumerate(input_points):
            current_points.append(point)
            if index % factor == 0:
                output_points.append(self.condense_points(current_points))
                current_points = []
        return output_points

    @staticmethod
    def geo_line(index, new, old):
        line = {
            'type': 'Feature',
            'properties': {
                'id': index,
                'elevation': new.get('altitude'),
                'speed': new.get('speed'),
                'distance': new.get('distance'),
                'cadence': new.get('cadence'),
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [
                        old.get('longitude'),
                        old.get('latitude'),
                    ],
                    [
                        new.get('longitude'),
                        new.get('latitude'),
                    ]
                ]
            }
        }
        if new.get('heart_rate') is not None:
            line['properties']['heart_rate'] = new.get('heart_rate')
        return line

    @staticmethod
    def geo_point(name, point):
        return {
            "type": "Feature",
            "properties": {
                "id": name,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    point.get('longitude'), point.get('latitude')
                ]
            }
        }

    def geo_json(self):
        data = []
        points = self.reduced_points()
        for index, point in enumerate(points):
            if index > 0:
                data.append(self.geo_line(index - 1, point, last_point))
            last_point = point
        first = points[0]
        last = points[-1]
        data.append(self.geo_point("progress", first))
        data.append(self.geo_point("start", first))
        data.append(self.geo_point("stop", last))
        return data

    @classmethod
    def trimp_activities(cls, user, start=None, end=None):
        activities = cls.objects.filter(owner=user).filter(trimp__isnull=False)
        if start is None:
            start = activities.order_by('time').first().time.date()
        else:
            activities = activities.filter(time__gte=start)
        if end is None:
            end = activities.order_by('time').last().time.date()
        else:
            activities = activities.filter(time__lte=end)
        return activities, start, end


class TrainingStressBalance(object):
    def __init__(self, start, end):
        self.data = {k: TrainingStressBalancePoint(k) for k in date_array(start, end)}

    def insert(self, activity):
        self.data[activity.time.date()].trimp += activity.trimp or 0

    def inflate(self):
        for index, point in enumerate(self.points()):
            if index != 0:
                point.increment_fitness(last_point)
            last_point = point

    def points(self):
        return sorted(self.data.values(), key=lambda h: h.date)

    @classmethod
    def history_for_user(cls, user, start=None, end=None):
        activities, start, end = Activity.trimp_activities(user, start, end)
        balance = cls(start, end)
        for activity in activities:
            balance.insert(activity)
        balance.inflate()
        return balance.points()


class TrainingStressBalancePoint(object):
    def __init__(self, date):
        self.date = date
        self.trimp = 0
        self.fitness = 0
        self.fatigue = 0
        self.form = 0

    def increment_fitness(self, last_point):
        self.fitness = (
            last_point.fitness + (self.trimp - last_point.fitness) * (1.0 - math.exp(-1.0 / 42.0))
        )
        self.fatigue = (
            last_point.fatigue + (self.trimp - last_point.fatigue) * (1.0 - math.exp(-1.0 / 7.0))
        )
        self.form = self.fitness - self.fatigue
