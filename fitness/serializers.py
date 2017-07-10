from django.contrib.auth.models import User
from rest_framework import serializers
from fitness.models import Activity


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff', 'profile')


class TrimpSerializer(serializers.Serializer):
    date = serializers.DateField()
    trimp = serializers.FloatField()
    fitness = serializers.FloatField()
    fatigue = serializers.FloatField()
    form = serializers.FloatField()


class ActivityDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time', 'geo_json', 'svg_points')


class ActivityListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time', 'id', 'trimp')
        read_only_fields = ('name', 'time', 'id', 'trimp')


class PointSerializer(serializers.Serializer):
    altitude = serializers.FloatField()
    cadence = serializers.FloatField(allow_null=True)
    distance = serializers.FloatField()
    heart_rate = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    speed = serializers.FloatField()
    time = serializers.DateTimeField()


class RunSerializer(serializers.Serializer):
    time = serializers.DateTimeField()
    name = serializers.CharField(max_length=64)
    points = PointSerializer(many=True)
    owner = UserSerializer(
        read_only=True,
        default=serializers.CreateOnlyDefault('Junk')
    )

    def validate_owner(self, value):
        return self.context['request'].user

    def create(self, validated_data):
        new_activity = Activity.objects.update_or_create(
            owner=validated_data['owner'],
            time=validated_data['time'],
            defaults=self.defaults(validated_data),
        )[0]
        new_activity.trimp = new_activity.calculate_trimp()
        new_activity.save()
        return new_activity

    def to_representation(self, item):
        return ActivityListSerializer(context=self.context).to_representation(item)

    @classmethod
    def defaults(cls, validated_data):
        points = validated_data['points']
        return {
            'name': validated_data['name'],
            'distance': max(
                a['distance'] for a in points
            ),
            'duration': cls.duration(points),
            'elevation': cls.elevation_gain(points),
            'data_points': len(points),
            'stream': cls.stream(points),
        }

    @staticmethod
    def duration(points):
        last = max(a['time'] for a in points)
        first = min(a['time'] for a in points)
        return (last - first).total_seconds()

    @staticmethod
    def elevation_gain(points):
        gain = 0
        last_elevation = None
        points_up = 0
        for point in points:
            if last_elevation is not None and point['altitude'] > last_elevation:
                if points_up < 2:
                    points_up += 1
                else:
                    gain += (int(point['altitude']) - int(last_elevation))
            else:
                points_up = 0
            last_elevation = point['altitude']
        return gain

    @staticmethod
    def stream(points):
        return {
            a['time'].isoformat(): a for a in sorted(points, key=lambda h: h['time'])
        }
