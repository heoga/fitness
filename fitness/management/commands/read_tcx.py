import glob
from django.core.management.base import BaseCommand, CommandError
from fitness.models import read_tcx


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