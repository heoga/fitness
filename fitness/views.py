import datetime
import pygal
import math
from pygal.style import NeonStyle

from django.http import HttpResponse

from fitness.models import Activity


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
    activities = Activity.objects.all()
    min_heart = 50
    max_heart = 203
    start = min(a.time.date() for a in activities)
    end = max(a.time.date() for a in activities)
    calendar = {k: DataPoint(k) for k in [
        (start + datetime.timedelta(days=i)) for i in range(0, (end - start).days + 1)
    ]}
    for activity in activities:
        print(activity.trimp(min_heart, max_heart))
        calendar[activity.time.date()].trimp += activity.trimp(min_heart, max_heart)
    points = sorted(calendar.values(), key=lambda h: h.date)
    for index, point in enumerate(points):
        if index != 0:
            point.increment_fitness(last_point)
        last_point = point
    dateline = pygal.DateLine(x_label_rotation=35, style=NeonStyle, legend_at_bottom=True, width=1024)
    dateline.title = 'Fitness over time'
    # datetimeline.x_labels = [a.date.isoformat() for a in points]
    dateline.add('Fitness', [(a.date, a.fitness) for a in points], dots_size=1)
    dateline.add('Fatigue', [(a.date, a.fatigue) for a in points], show_dots=False)
    dateline.add('Form', [(a.date, a.form) for a in points], show_dots=False)
    # with open(r'C:\Users\karlo\sample.svg', 'wb') as h:
    #    h.write(dateline.render())
    # return HttpResponse(dateline.render())
    return dateline.render_django_response()


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
