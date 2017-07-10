from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy

from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin

from . import forms
from . import models
from . import serializers


class ActivityList(LoginRequiredMixin, ListView):
    template_name = 'fitness/activity_list.html'
    model = models.Activity
    paginate_by = 30

    def get_queryset(self):
        return models.Activity.objects.filter(owner=self.request.user)


class ActivityDetail(LoginRequiredMixin, DetailView):
    template_name = 'fitness/activity_detail.html'
    model = models.Activity

    def get_queryset(self):
        return models.Activity.objects.filter(owner=self.request.user)


class ActivitySVG(LoginRequiredMixin, DetailView):
    template_name = 'fitness/activity.svg'
    model = models.Activity

    def get_queryset(self):
        return models.Activity.objects.filter(owner=self.request.user)


class ActivityViewSet(
    RetrieveModelMixin, ListModelMixin, CreateModelMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        return models.Activity.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        return {
            'retrieve': serializers.ActivityDetailSerializer,
            'create': serializers.RunSerializer
        }.get(self.action) or serializers.ActivityListSerializer


class TrimpViewSet(viewsets.ViewSet):
    queryset = models.Activity.objects.all()

    def list(self, request):
        serializer = serializers.TrimpSerializer(
            models.Activity.trimp_history(self.request.user),
            many=True, context={'request': request}
        )
        return Response(serializer.data)


class ControlPanelView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')
    template_name = "fitness/control_panel.html"

    def get(self, request, *args, **kwargs):
        user_form = forms.UserForm(initial={
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'email': self.request.user.email,
        })
        profile_form = forms.ProfileForm(initial={
            'theme': self.request.user.profile.theme,
            'gender': self.request.user.profile.gender,
        })
        heart_form = forms.HeartRateForm(initial={
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
        user_form = forms.UserForm(request.POST)
        profile_form = forms.ProfileForm(request.POST)
        heart_form = forms.HeartRateForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid() and heart_form.is_valid():
            for key, value in user_form.cleaned_data.items():
                setattr(self.request.user, key, value)
            for key, value in profile_form.cleaned_data.items():
                setattr(self.request.user.profile, key, value)
            for key, value in heart_form.cleaned_data.items():
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
        activity = models.Activity.objects.filter(owner=request.user, id=id).first()
        if activity:
            activity.trimp = activity.calculate_trimp()
            activity.save()
        return HttpResponse('Done')


