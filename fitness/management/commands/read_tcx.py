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
                for activity in activities:
                    self.stdout.write(self.style.SUCCESS(
                        'Added {} {}'.format(activity.name, activity.time)
                    ))


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
            saved_lap = False
            for index, xml_lap in enumerate(xml_activity.findall('default:Lap', NAMESPACES), start=1):
                lap = Lap(activity=activity, lap=index)
                lap.save()
                saved_point = False
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
                            heart_rate = None
                        extensions = xml_point.find('default:Extensions', NAMESPACES)
                        tpx = extensions.find('extension:TPX', NAMESPACES)
                        try:
                            cadence = tpx.find('extension:RunCadence', NAMESPACES).text
                        except AttributeError:
                            cadence = None
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
                        saved_point = True
                if not saved_point:
                    lap.delete()
                else:
                    saved_lap = True
            if not saved_lap:
                activity.delete()
    return activities