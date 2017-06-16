from rest_framework import serializers

from fitness.models import Activity, Lap, Point


class ActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time', 'laps', 'geo_json', 'svg_points')


class LapSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lap
        fields = ('url', 'activity', 'lap', 'points')


class PointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Point
        fields = ('url', 'lap', 'time', 'latitude', 'longitude', 'altitude', 'heart_rate', 'cadence')