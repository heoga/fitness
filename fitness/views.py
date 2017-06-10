import datetime
import pygal
import math
from pygal.style import NeonStyle

from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from rest_framework import viewsets

from fitness.models import Activity, Lap, Point
from fitness.serializers import ActivitySerializer, LapSerializer, PointSerializer


class ActivityList(ListView):
    template_name = 'fitness/activity_list.html'
    model = Activity


class ActivityDetail(DetailView):
    template_name = 'fitness/activity_detail.html'
    model = Activity


class ActivitySVG(DetailView):
    template_name = 'fitness/activity.svg'
    model = Activity


class ActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer


class LapViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Lap.objects.all()
    serializer_class = LapSerializer


class PointViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Point.objects.all()
    serializer_class = PointSerializer



class DataPoint(object):
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


def render_trimp(request):
    activities = [a for a in Activity.objects.all() if a.points_with_heart_rate()]
    min_heart = 50
    max_heart = 203
    start = min(a.time.date() for a in activities)
    end = max(a.time.date() for a in activities)
    calendar = {k: DataPoint(k) for k in [
        (start + datetime.timedelta(days=i)) for i in range(0, (end - start).days + 1)
    ]}
    for activity in activities:
        calendar[activity.time.date()].trimp += activity.trimp(min_heart, max_heart)
    points = sorted(calendar.values(), key=lambda h: h.date)
    for index, point in enumerate(points):
        if index != 0:
            point.increment_fitness(last_point)
        last_point = point
    dateline = pygal.DateLine(x_label_rotation=35, style=NeonStyle, legend_at_bottom=True, width=1024)
    dateline.title = 'Fitness over time'
    dateline.add('Fitness', [(a.date, a.fitness) for a in points], dots_size=1)
    dateline.add('Fatigue', [(a.date, a.fatigue) for a in points], show_dots=False)
    dateline.add('Form', [(a.date, a.form) for a in points], show_dots=False)
    return dateline.render_django_response()


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
