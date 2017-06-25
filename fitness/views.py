import datetime
import pygal
import math
from pygal.style import NeonStyle

from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from rest_framework import viewsets
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy

from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from fitness.forms.profile import ProfileForm
from fitness.forms.user import UserForm

from fitness.models import Activity
from fitness.serializers import ActivitySerializer


class ActivityList(ListView):
    template_name = 'fitness/activity_list.html'
    model = Activity
    paginate_by = 30


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


class ControlPanelView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')
    template_name = "fitness/control_panel.html"

    def get(self, request, *args, **kwargs):
        user_form = UserForm(initial={
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'email': self.request.user.email,
        })
        profile_form = ProfileForm(initial={
            'theme': self.request.user.profile.theme
        })
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
            'view': self,
        })

    def post(self, request, *args, **kwargs):
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            for key, value in user_form.cleaned_data.items():
                setattr(self.request.user, key, value)
            for key, value in profile_form.cleaned_data.items():
                setattr(self.request.user.profile, key, value)
            self.request.user.save()
            self.request.user.profile.save()
        return self.get(request, *args, **kwargs)


class UploadView(TemplateView):
    template_name = 'fitness/activity_upload.html'

