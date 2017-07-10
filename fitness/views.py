import datetime
import pygal
import math
from pygal.style import NeonStyle

from django.views.generic import ListView, DetailView
from rest_framework import viewsets
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework import status
from rest_framework.settings import api_settings

from fitness.forms.profile import ProfileForm, HeartRateForm
from fitness.forms.user import UserForm

from fitness.models import Activity
from fitness.serializers import ActivityDetailSerializer, ActivityListSerializer, TrimpSerializer, RunSerializer


class ActivityList(LoginRequiredMixin, ListView):
    template_name = 'fitness/activity_list.html'
    model = Activity
    paginate_by = 30

    def get_queryset(self):
        return Activity.objects.filter(owner=self.request.user)


class ActivityDetail(LoginRequiredMixin, DetailView):
    template_name = 'fitness/activity_detail.html'
    model = Activity

    def get_queryset(self):
        return Activity.objects.filter(owner=self.request.user)


class ActivitySVG(LoginRequiredMixin, DetailView):
    template_name = 'fitness/activity.svg'
    model = Activity

    def get_queryset(self):
        return Activity.objects.filter(owner=self.request.user)


class ActivityViewSet(
    RetrieveModelMixin, ListModelMixin, CreateModelMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        return Activity.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        return {
            'retrieve': ActivityDetailSerializer,
            'create': RunSerializer
        }.get(self.action) or ActivityListSerializer


class TrimpViewSet(viewsets.ViewSet):
    queryset = Activity.objects.all()

    def list(self, request):
        serializer = TrimpSerializer(
            Activity.trimp_history(self.request.user),
            many=True, context={'request': request}
        )
        return Response(serializer.data)


@login_required
def render_trimp(request):
    points = Activity.trimp_history(request.user)
    dateline = pygal.DateLine(x_label_rotation=35, style=NeonStyle, legend_at_bottom=True, width=1024)
    dateline.title = 'Fitness over time'
    dateline.add('Fitness', [(a.date, a.fitness) for a in points], dots_size=1)
    dateline.add('Fatigue', [(a.date, a.fatigue) for a in points], show_dots=False)
    dateline.add('Form', [(a.date, a.form) for a in points], show_dots=False)
    return dateline.render_django_response()


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
            'theme': self.request.user.profile.theme,
            'gender': self.request.user.profile.gender,
        })
        heart_form = HeartRateForm(initial={
            'minimum_heart_rate': self.request.user.profile.minimum_heart_rate,
            'maximum_heart_rate': self.request.user.profile.maximum_heart_rate
        })
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
            'heart_form': heart_form,
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


class UploadView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness/activity_upload.html'


class TrimpView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness/trimp.html'


class RecalculateTRIMPView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        id = kwargs['pk']
        activity = Activity.objects.filter(owner=request.user, id=id).first()
        if activity:
            activity.trimp = activity.calculate_trimp()
            activity.save()
        return HttpResponse('Done')


