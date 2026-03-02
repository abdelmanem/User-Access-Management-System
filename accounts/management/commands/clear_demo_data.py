from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import CustomUser
from hardware.models import HardwareAsset
from systems.models import System
from access_management.models import UserSystemAccess


class Command(BaseCommand):
    help = "Delete all records from CustomUser, HardwareAsset, System and UserSystemAccess tables."
        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    )

    def add_arguments(self, parser):
/*************  ✨ Windsurf Command ⭐  *************/
    """
    Add the following optional arguments to the parser:

    --keep-superusers: Do not delete users with is_superuser=True.
    --noinput: Do not prompt for confirmation.
    """
/*******  2bf72ca6-4dc0-4807-82be-d54cf8b2d8cf  *******/
        parser.add_argument(
            '--keep-superusers',
            action='store_true',
            help='Do not delete users with is_superuser=True',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Do not prompt for confirmation',
        )

    def handle(self, *args, **options):
        keep_su = options['keep_superusers']
        noinput = options['noinput']

        if not noinput:
            prompt = (
                "This command will delete ALL records from the following models:\n"
                "  - CustomUser (optionally excluding superusers)\n"
                "  - HardwareAsset\n"
                "  - System\n"
                "  - UserSystemAccess\n"
                "\nAre you sure you want to continue? [y/N]: "
            )
            confirm = input(prompt)
            if confirm.lower() not in ('y', 'yes'):
                self.stdout.write(self.style.NOTICE('Aborted.'))
                return

        with transaction.atomic():
            # delete access assignments first (depends on users/systems)
            accesses = UserSystemAccess.objects.all()
            count = accesses.count()
            if count:
                accesses.delete()
                self.stdout.write(f"Deleted {count} UserSystemAccess records.")

            hw = HardwareAsset.objects.all()
            count = hw.count()
            if count:
                hw.delete()
                self.stdout.write(f"Deleted {count} HardwareAsset records.")

            systems = System.objects.all()
            count = systems.count()
            if count:
                systems.delete()
                self.stdout.write(f"Deleted {count} System records.")

            users_qs = CustomUser.objects.all()
            if keep_su:
                users_qs = users_qs.exclude(is_superuser=True)
            count = users_qs.count()
            if count:
                users_qs.delete()
                self.stdout.write(f"Deleted {count} CustomUser records.")

        self.stdout.write(self.style.SUCCESS('Data clearance complete.'))
