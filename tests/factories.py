from django.db.models.signals import post_save

import factory

from fitness.models import User, Profile, Activity, create_user_profile


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory('factories.UserFactory', profile=None)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    profile = factory.RelatedFactory(ProfileFactory, 'user')

    @classmethod
    def _generate(cls, create, attrs):
        """Override the default _generate() to disable the post-save signal."""

        # Note: If the signal was defined with a dispatch_uid, include that in both calls.
        post_save.disconnect(create_user_profile, User)
        user = super(UserFactory, cls)._generate(create, attrs)
        post_save.connect(create_user_profile, User)
        return user


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    owner = factory.SubFactory(UserFactory)