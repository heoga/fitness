from rest_framework import serializers

from fitness.models import Activity


class ActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time', 'geo_json', 'svg_points')