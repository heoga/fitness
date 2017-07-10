from django.contrib.auth.models import User
from django.forms import ModelForm

from fitness.models import Profile


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['theme', 'gender']


class HeartRateForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['minimum_heart_rate', 'maximum_heart_rate']


class UserForm(ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
