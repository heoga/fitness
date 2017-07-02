from django.forms import ModelForm
from fitness.models import Profile


class ProfileForm(ModelForm):

    class Meta:
        model = Profile
        fields = ['theme', 'gender', 'minimum_heart_rate', 'maximum_heart_rate']
