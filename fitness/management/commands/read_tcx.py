import glob
import xml.etree.ElementTree as ET
import dateutil.parser
from django.core.management.base import BaseCommand

from fitness.models import Activity, Lap, Point

NAMESPACES = {
    'default': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
    'extension': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
}


class Command(BaseCommand):
    help = 'Add TCX Files'

    def add_arguments(self, parser):
        parser.add_argument('tcx', nargs='+')

    def handle(self, *args, **options):
        for entry in options['tcx']:
            for filename in glob.glob(entry):
                activities = read_tcx(filename)
                for activity, created in activities:
                    note = 'Added' if created else 'Modified'
                    self.stdout.write(self.style.SUCCESS(
                        '{} {} {}'.format(note, activity.name, activity.time)
                    ))


def read_tcx(filename):
    tree = ET.parse(filename)
    tcx = tree.getroot()
    activities = []
    for activity_list in tcx.findall('default:Activities', NAMESPACES):
        for xml_activity in activity_list.findall('default:Activity', NAMESPACES):
            name = xml_activity.find('default:Notes', NAMESPACES).text
            start = dateutil.parser.parse(xml_activity.find('default:Id', NAMESPACES).text)
            # if Activity.objects.filter(time=start):
            #    continue
            activity, created = Activity.objects.update_or_create(name=name, time=start)
            activities.append((activity, created))
            saved_lap = False
            last_time = None
            last_distance = 0.0
            for index, xml_lap in enumerate(xml_activity.findall('default:Lap', NAMESPACES), start=1):
                lap, unused = Lap.objects.update_or_create(activity=activity, lap=index)
                saved_point = False
                for xml_track in xml_lap.findall('default:Track', NAMESPACES):
                    for xml_point in xml_track.findall('default:Trackpoint', NAMESPACES):
                        try:
                            time = dateutil.parser.parse(xml_point.find('default:Time', NAMESPACES).text)
                            position = xml_point.find('default:Position', NAMESPACES)
                            latitude = float(position.find('default:LatitudeDegrees', NAMESPACES).text)
                            longitude = float(position.find('default:LongitudeDegrees', NAMESPACES).text)
                            altitude = float(xml_point.find('default:AltitudeMeters', NAMESPACES).text)
                            distance = float(xml_point.find('default:DistanceMeters', NAMESPACES).text)
                        except AttributeError:
                            continue
                        if time == last_time:
                            continue
                        try:
                            heart_rate = xml_point.find('default:HeartRateBpm', NAMESPACES).find('default:Value', NAMESPACES).text
                        except AttributeError:
                            heart_rate = None
                        extensions = xml_point.find('default:Extensions', NAMESPACES)
                        tpx = extensions.find('extension:TPX', NAMESPACES)
                        try:
                            cadence = tpx.find('extension:RunCadence', NAMESPACES).text
                        except AttributeError:
                            cadence = None
                        if last_time is not None:
                            try:
                                seconds = (time - last_time).total_seconds()
                                speed = (distance - last_distance) / seconds
                            except:
                                print(filename, time)
                                raise
                        else:
                            speed = 0.0
                        matching_points = Point.objects.filter(lap=lap, time=time)
                        if matching_points.count() > 1:
                            for point in matching_points:
                                point.delete()
                        point, unused = Point.objects.update_or_create(
                            lap=lap,
                            time=time,
                            defaults={
                                'latitude': latitude,
                                'longitude': longitude,
                                'altitude': altitude,
                                'heart_rate': heart_rate,
                                'cadence': cadence,
                                'distance': distance,
                                'speed': speed,
                            }
                        )
                        saved_point = True
                        last_time = time
                        last_distance = distance
                if not saved_point:
                    lap.delete()
                else:
                    saved_lap = True
            if not saved_lap:
                activity.delete()
    return activities