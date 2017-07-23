import datetime

import pytest
from django_mock_queries.query import MockSet, MockModel

import fitness.models as models

from factories import UserFactory, ProfileFactory, ActivityFactory


def timedelta(time, seconds):
    return time + datetime.timedelta(seconds=seconds)


def test_average():
    assert models.average(1, 2, 3, 4, 5) == 3


def test_date_array():
    assert models.date_array(datetime.date(2015, 4, 3), datetime.date(2015, 4, 9)) == [
        datetime.date(2015, 4, 3),
        datetime.date(2015, 4, 4),
        datetime.date(2015, 4, 5),
        datetime.date(2015, 4, 6),
        datetime.date(2015, 4, 7),
        datetime.date(2015, 4, 8),
        datetime.date(2015, 4, 9),
    ]


def test_delta_minutes():
    assert models.delta_minutes(
        datetime.datetime(2015, 4, 3, 5, 7, 0), datetime.datetime(2015, 4, 3, 5, 5, 30)
    ) == 1.5


def test_heart_rate_reserve():
    assert models.heart_rate_reserve(102, 50, 130) == 0.4
    assert models.heart_rate_reserve(20, 50, 130) == 0.0
    assert models.heart_rate_reserve(200, 50, 130) == 1.0


def test_height_coordinate():
    assert models.height_coordinate(10, 5, 20, 30) == 7.5


def test_range_and_average():
    assert models.range_and_average([1, 2, 3, 4, 5]) == (4, 3)


def test_width_coordinate():
    assert models.width_coordinate(10, 5, 20, 30) == 22.5


def test_theme_name():
    assert '{}'.format(models.Theme(name='some name')) == 'Some Name'


def test_profile_heart_rate(mocker):
    profile = ProfileFactory.build()
    assert profile.minimum_heart_rate == 60
    assert profile.maximum_heart_rate == 190
    assert profile.heart_rate_reserve() == 130
    profile.minimum_heart_rate = 50
    profile.maximum_heart_rate = 200
    assert profile.heart_rate_reserve() == 150
    profile.minimum_heart_rate = -1
    profile.maximum_heart_rate = -3
    mocker.patch.object(models.models.Model, 'save')
    profile.save()
    assert profile.minimum_heart_rate == 1
    assert profile.maximum_heart_rate == 2


def test_profile_percent_reserve(mocker):
    profile = ProfileFactory.build()
    mocker.patch.object(profile, 'heart_rate_reserve', return_value=100)
    assert profile.percent_of_heart_rate_reserve(100) == 0.4


def test_activity_timezone_finder():
    activity = ActivityFactory.build(
        time=datetime.datetime(2015, 4, 3, 7, 5, tzinfo=datetime.timezone.utc)
    )
    activity.stream = {
        'data': {'latitude': 39.7, 'longitude': -105},
    }
    assert activity.local_time() == '03 April 2015 at 01:05'
    activity.stream = {
        'data': {'latitude': 0.0, 'longitude': 0.0},
    }
    assert activity.local_time() == '03 April 2015 at 07:05'


def test_points_with_heart_rate(mocker):
    activity = ActivityFactory.build()
    mocker.patch.object(activity, 'point_stream', return_value=[
        {'alpha': 1},
        {'beta': 2, 'heart_rate': 3},
        {'delta': 4, 'heart_rate': 0},
        {'gamma': 6},
    ])
    assert list(set(a.keys()) for a in activity.points_with_heart_rate()) == [
        {'beta', 'heart_rate'},
    ]


def test_delta_trimp(mocker):
    activity = ActivityFactory.build()
    mocker.patch.object(activity.owner.profile, 'percent_of_heart_rate_reserve', return_value=0.5)
    activity.owner.profile.gender = 'M'
    assert round(activity.delta_trimp(
        datetime.datetime(2017, 4, 3, 7, 33, 0),
        datetime.datetime(2017, 4, 3, 7, 30, 0),
        120,
        130,
    ), 3) == 2.507


def test_calculate_trimp(mocker):
    activity = ActivityFactory.build()
    points = mocker.patch.object(activity, 'points_with_heart_rate', return_value=[])
    delta = mocker.patch.object(activity, 'delta_trimp', return_value=2)
    assert activity.calculate_trimp() is None
    assert delta.call_count == 0
    now = datetime.datetime.now()
    hr_points = [
        {'time': timedelta(now, 0), 'heart_rate': 130},
        {'time': timedelta(now, 10), 'heart_rate': 130},
        {'time': timedelta(now, 20), 'heart_rate': 130},
        {'time': timedelta(now, 30), 'heart_rate': 130},
    ]
    points.return_value = hr_points
    assert activity.calculate_trimp() == 6
    assert delta.call_count == 3
    delta.assert_any_call(
        hr_points[2]['time'], hr_points[1]['time'], hr_points[2]['heart_rate'], hr_points[1]['heart_rate']
    )


def test_decompress():
    good = {
        'time': datetime.datetime(2017, 5, 4, 3, 2, 1)
    }
    bad = {
        'time': '2017-05-04T03:02:01'
    }
    assert models.Activity.decompress(good) == good
    assert models.Activity.decompress(bad) == good


def test_point_stream():
    activity = ActivityFactory.build()
    stream_data = {
        'point1': {
            'time': '2017-05-04T03:02:03'
        },
        'point2': {
            'time': '2017-05-04T03:02:01'
        },
        'point3': {
            'time': '2017-05-04T03:02:02'
        },
    }
    activity.stream = stream_data
    assert activity.point_stream() == [
        {
            'time': datetime.datetime(2017, 5, 4, 3, 2, 1)
        }, {
            'time': datetime.datetime(2017, 5, 4, 3, 2, 2)
        }, {
            'time': datetime.datetime(2017, 5, 4, 3, 2, 3)
        }
    ]


def test_track(mocker):
    activity = ActivityFactory.build()
    stream_data = [
        {
            'latitude': 40,
            'longitude': 45,
            'something': 'Else',
        }, {
            'latitude': 30,
            'longitude': 35,
            'something': 'Else',
        }, {
            'latitude': 20,
            'longitude': 25,
            'something': 'Else',
        }
    ]
    mocker.patch.object(activity, 'point_stream', return_value=stream_data)
    assert activity.track() == [(40, 45), (30, 35), (20, 25)]


def test_adjusted_track(mocker):
    activity = ActivityFactory.build()
    track = [(40, 45), (30, 35), (20, 25)]
    mocker.patch.object(activity, 'track', return_value=track)
    adjusted = activity.adjusted_track()
    assert all(len(a) == 2 for a in adjusted)
    assert [a[0] for a in adjusted] == [40, 30, 20]
    assert [round(a[1], 4) for a in adjusted] == [34.472, 26.8116, 19.1511]


def test_svg_points(mocker):
    activity = ActivityFactory.build()
    track = [(40, 45), (30, 35), (20, 25)]
    mocker.patch.object(activity, 'adjusted_track', return_value=track)
    assert activity.svg_points() == [(30.0, 0.0), (15.0, 15.0), (0.0, 30.0)]
    assert activity.svg_points(height=10, width=40) == [(40.0, 0.0), (20.0, 5.0), (0.0, 10.0)]


def test_display_distance():
    activity = ActivityFactory.build(distance=1300)
    assert activity.display_distance() == 1.3
    assert activity.display_distance(unit='m') == 1300


def test_duration_as_string():
    activity = ActivityFactory.build(duration=665)
    assert activity.duration_as_string() == '11:05'
    activity.duration = 4265
    assert activity.duration_as_string() == '1:11:05'


def test_average_pace(mocker):
    activity = ActivityFactory.build(duration=720)
    mocker.patch.object(activity, 'display_distance', return_value=0)
    assert activity.average_pace() == 0
    activity.display_distance.return_value = 6
    assert activity.average_pace() == 2.0


def test_average_pace_as_string(mocker):
    activity = ActivityFactory.build()
    mocker.patch.object(activity, 'average_pace', return_value=2.5)
    assert activity.average_pace_as_string() == '2:30'


def test_has_heart_rate(mocker):
    activity = ActivityFactory.build()
    mocker.patch.object(activity, 'points_with_heart_rate', return_value=[])
    assert activity.has_heart_rate() is False
    activity.points_with_heart_rate.return_value = [1]
    assert activity.has_heart_rate() is True


def test_activity_average():
    points = [
        {
            'time': datetime.datetime(2017, 4, 3, 2, 1, 5),
            'distance': 1,
            'speed': 3,
        }, {
            'time': datetime.datetime(2017, 4, 3, 2, 3, 5),
            'distance': 3,
        }, {
            'time': datetime.datetime(2017, 4, 3, 2, 4, 5),
            'distance': 5,
            'speed': 3,
        },
    ]
    assert models.Activity.average(points, 'time') == datetime.datetime(2017, 4, 3, 2, 1, 5)
    assert models.Activity.average(points, 'distance') == 3
    assert models.Activity.average(points, 'speed') == 2
    assert models.Activity.average(points, 'grade') is None


def test_condense_points():
    points = [
        {
            'time': datetime.datetime(2017, 4, 3, 2, 1, 5),
            'distance': 1,
            'speed': 3,
        }, {
            'time': datetime.datetime(2017, 4, 3, 2, 3, 5),
            'distance': 3,
        }, {
            'time': datetime.datetime(2017, 4, 3, 2, 4, 5),
            'distance': 5,
            'speed': 3,
        },
    ]
    assert models.Activity.condense_points(points) == {
        'time': datetime.datetime(2017, 4, 3, 2, 1, 5),
        'distance': 3,
        'speed': 2,
    }


def test_reduction_factor():
    assert models.Activity.reduction_factor([''] * 199) == 1
    assert models.Activity.reduction_factor([''] * 399) == 1
    assert models.Activity.reduction_factor([''] * 401) == 2


def test_reduced_points(mocker):
    activity = ActivityFactory.build()
    mocker.patch.object(activity, 'point_stream', return_value=list(range(0, 20)))
    mocker.patch.object(activity, 'reduction_factor', return_value=2)
    mocker.patch.object(activity, 'condense_points', side_effect=lambda h: sum(h))
    assert activity.reduced_points() == [0, 3, 7, 11, 15, 19, 23, 27, 31, 35]


def test_geo_line():
    new_point = {
        'altitude': 100,
        'speed': 20,
        'distance': 10,
        'cadence': 120,
        'longitude': 50,
        'latitude': 40,
    }
    old_point = {
        'longitude': 51,
        'latitude': 39,
    }
    expected = {
        'geometry': {
            'coordinates': [[51, 39], [50, 40]],
            'type': 'LineString'
        },
        'properties': {
            'cadence': 120,
            'distance': 10,
            'elevation': 100,
            'id': 4,
            'speed': 20
        },
        'type': 'Feature'
    }
    assert models.Activity.geo_line(4, new_point, old_point) == expected
    new_point['heart_rate'] = 150
    expected['properties']['heart_rate'] = 150
    assert models.Activity.geo_line(4, new_point, old_point) == expected


def test_geo_point():
    new_point = {
        'altitude': 100,
        'speed': 20,
        'distance': 10,
        'cadence': 120,
        'longitude': 50,
        'latitude': 40,
    }
    assert models.Activity.geo_point(4, new_point) == {
        'geometry': {
            'coordinates': [50, 40],
            'type': 'Point'
        },
        'properties': {
            'id': 4,
        },
        'type': 'Feature'
    }


def test_geo_json(mocker):
    def pass_through(*args):
        return args
    activity = ActivityFactory.build()
    mocker.patch.object(activity, 'reduced_points', return_value=['P{}'.format(i) for i in range(0, 5)])
    mocker.patch.object(activity, 'geo_line', side_effect=pass_through)
    mocker.patch.object(activity, 'geo_point', side_effect=pass_through)
    assert activity.geo_json() == [
        (0, 'P1', 'P0'),
        (1, 'P2', 'P1'),
        (2, 'P3', 'P2'),
        (3, 'P4', 'P3'),
        ('progress', 'P0'),
        ('start', 'P0'),
        ('stop', 'P4')
    ]


def test_trimp_activities(mocker):
    user_a = UserFactory.build()
    user_b = UserFactory.build()
    all_activities = MockSet()
    mocker.patch.object(models.Activity, 'objects', all_activities)
    all_activities.add(
        MockModel(owner=user_b, trimp=100, time=datetime.datetime(2017, 5, 4, 3, 2, 1)),
        MockModel(owner=user_a, trimp=100, time=datetime.datetime(2017, 5, 5, 4, 2, 1)),
        MockModel(owner=user_a, trimp=None, time=datetime.datetime(2017, 5, 6, 5, 2, 1)),
        MockModel(owner=user_a, trimp=100, time=datetime.datetime(2017, 5, 7, 6, 2, 1)),
        MockModel(owner=user_a, trimp=100, time=datetime.datetime(2017, 5, 8, 6, 2, 1)),
        MockModel(owner=user_a, trimp=100, time=datetime.datetime(2017, 5, 9, 7, 2, 1)),
        MockModel(owner=user_b, trimp=100, time=datetime.datetime(2017, 5, 10, 8, 2, 1)),
    )
    activities, start, end = models.Activity.trimp_activities(user_a)
    assert set(a.time.day for a in activities) == {5, 7, 8, 9}
    assert start.day == 5
    assert end.day == 9
    activities, start, end = models.Activity.trimp_activities(
        user_a, start=datetime.datetime(2017, 5, 5, 10, 5, 5), end=datetime.datetime(2017, 5, 8, 10, 5, 5)
    )
    assert set(a.time.day for a in activities) == {7, 8}
    assert start.day == 5
    assert end.day == 8


def test_balance_point():
    point = models.TrainingStressBalancePoint(datetime.datetime(2017, 4, 3, 5, 4, 2))
    assert point.date == datetime.datetime(2017, 4, 3, 5, 4, 2)
    assert point.trimp == 0
    assert point.fitness == 0
    assert point.fatigue == 0
    assert point.form == 0

    old_point = models.TrainingStressBalancePoint(datetime.datetime(2017, 4, 3, 5, 4, 1))
    old_point.fitness = 20
    old_point.fatigue = 30

    point.trimp = 120
    point.increment_fitness(old_point)
    assert round(point.fitness, 4) == 22.3528
    assert round(point.fatigue, 4) == 41.981
    assert round(point.form, 4) == -19.6282


def test_balance():
    balance = models.TrainingStressBalance(datetime.date(2017, 4, 3), datetime.date(2017, 4, 7))
    assert [a.trimp for a in balance.data.values()] == [0, 0, 0, 0, 0]
    activity = ActivityFactory.build(time=datetime.datetime(2017, 4, 5, 3, 2, 1), trimp=100)
    balance.insert(activity)
    assert balance.data[datetime.date(2017, 4, 5)].trimp == 100
    assert [a.fitness for a in balance.data.values()] == [0, 0, 0, 0, 0]
    balance.inflate()
    assert [round(a.fitness, 3) for a in sorted(balance.data.values(), key=lambda h: h.date)] == [
        0, 0.0, 2.353, 2.297, 2.243
    ]


def test_trimp_history(mocker):
    trimp = mocker.patch.object(models.Activity, 'trimp_activities', return_value=(
        range(0, 4), datetime.date(2017, 4, 3), datetime.date(2017, 4, 7)
    ))
    insertions = mocker.patch.object(models.TrainingStressBalance, 'insert')
    inflations = mocker.patch.object(models.TrainingStressBalance, 'inflate')
    mocker.patch.object(models.TrainingStressBalance, 'points', return_value='trimp_data')
    assert models.TrainingStressBalance.history_for_user('user') == 'trimp_data'
    trimp.assert_called_once_with('user', None, None)
    for i in range(0, 4):
        insertions.assert_any_call(i)
    inflations.assert_called_once_with()
    trimp.reset_mock()
    models.TrainingStressBalance.history_for_user(
        'user', start=datetime.date(2017, 4, 6), end=datetime.date(2017, 4, 8)
    )
    trimp.assert_called_once_with('user', datetime.date(2017, 4, 6), datetime.date(2017, 4, 8))






