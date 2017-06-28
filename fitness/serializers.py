from rest_framework import serializers

from fitness.models import Activity


class ActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time', 'geo_json', 'svg_points')


class BareActivitySerializer(serializers.Serializer):
    class Meta:
        model = Activity
        fields = ('url', 'name', 'time')


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

    def is_valid(self, raise_exception=False):
        print(self.initial_data)
        return super(RunSerializer, self).is_valid(raise_exception)

    def create(self, validated_data):
        points = validated_data['points']
        return Activity.objects.create(
            name=validated_data['name'],
            time=validated_data['time'],
            distance=max(
                a['distance'] for a in points
            ),
            duration=self.duration(points),
            elevation=self.elevation_gain(points),
            data_points=len(points),
            stream=self.stream(points),
        )

    def to_representation(self, item):
        return BareActivitySerializer().to_representation(item)

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
        ordered_points = sorted(
            points, key=lambda h: h['time']
        )
        return {
            a['time'].isoformat(): a for a in ordered_points
        }
        return {
            a.time.isoformat(): {
                'time': a.time,
                'latitude': a.latitude,
                'longitude': a.longitude,
                'altitude': a.altitude,
                'heart_rate': a.heart_rate,
                'cadence': a.cadence,
                'distance': a.distance,
                'speed': a.speed,
            } for a in ordered_points
        }
