import math
import xml.etree.ElementTree as ET

import dateutil.parser

from django.db import models


class Activity(models.Model):
    name = models.CharField(max_length=128)
    time = models.DateTimeField()

    def trimp(self, minimum, maximum, male=True):
        trimp = 0
        last_point = None
        heart_range = maximum - minimum
        exponent = 1.92 if male else 1.67
        for lap in self.lap_set.all().order_by('lap'):
            for point in lap.point_set.all().order_by('time'):
                if last_point is not None:
                    minutes = (point.time - last_point.time).total_seconds() / 60.0
                    average_heart_rate = (point.heart_rate + last_point.heart_rate) / 2
                    reserve = max((average_heart_rate - minimum) / heart_range, 0)
                    trimp += (
                        minutes * reserve * 0.64 * math.exp(exponent * reserve)
                    )
                last_point = point
        return trimp


class Lap(models.Model):
    activity = models.ForeignKey(Activity)
    lap = models.IntegerField()


class Point(models.Model):
    lap = models.ForeignKey(Lap)
    time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    heart_rate = models.FloatField()
    cadence = models.FloatField()

NAMESPACES = {
    'default': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
    'extension': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
}


def read_tcx(filename):
    tree = ET.parse(filename)
    tcx = tree.getroot()
    activities = []
    for activity_list in tcx.findall('default:Activities', NAMESPACES):
        for xml_activity in activity_list.findall('default:Activity', NAMESPACES):
            name = xml_activity.find('default:Notes', NAMESPACES).text
            start = dateutil.parser.parse(xml_activity.find('default:Id', NAMESPACES).text)
            if Activity.objects.filter(time=start):
                continue
            activity = Activity(name=name, time=start)
            activity.save()
            activities.append(activity)
            for index, xml_lap in enumerate(xml_activity.findall('default:Lap', NAMESPACES), start=1):
                lap = Lap(activity=activity, lap=index)
                lap.save()
                for xml_track in xml_lap.findall('default:Track', NAMESPACES):
                    for xml_point in xml_track.findall('default:Trackpoint', NAMESPACES):
                        try:
                            time = dateutil.parser.parse(xml_point.find('default:Time', NAMESPACES).text)
                            position = xml_point.find('default:Position', NAMESPACES)
                            latitude = position.find('default:LatitudeDegrees', NAMESPACES).text
                            longitude = position.find('default:LongitudeDegrees', NAMESPACES).text
                            altitude = xml_point.find('default:AltitudeMeters', NAMESPACES).text
                        except AttributeError:
                            continue
                        try:
                            heart_rate = xml_point.find('default:HeartRateBpm', NAMESPACES).find('default:Value', NAMESPACES).text
                        except AttributeError:
                            heart_rate = 0
                        extensions = xml_point.find('default:Extensions', NAMESPACES)
                        tpx = extensions.find('extension:TPX', NAMESPACES)
                        cadence = tpx.find('extension:RunCadence', NAMESPACES).text
                        point = Point(
                            lap=lap,
                            time=time,
                            latitude=latitude,
                            longitude=longitude,
                            altitude=altitude,
                            heart_rate=heart_rate,
                            cadence=cadence
                        )
                        point.save()
    return activities