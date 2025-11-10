import csv
from django.contrib.auth import get_user_model
from django.db import transaction
from departments.models import Department
from systems.models import System

User = get_user_model()


def import_users_from_csv(file):
    """Imports user data from a CSV file."""
    reader = csv.DictReader(file)
    with transaction.atomic():
        for row in reader:
            User.objects.create_user(
                username=row['username'],
                email=row['email'],
                password=row['password'],
                first_name=row['first_name'],
                last_name=row['last_name'],
            )

def import_departments_from_csv(file):
    """Imports department data from a CSV file."""
    reader = csv.DictReader(file)
    with transaction.atomic():
        for row in reader:
            Department.objects.create(
                name=row['name'],
                description=row['description'],
            )

def import_systems_from_csv(file):
    """Imports system data from a CSV file."""
    reader = csv.DictReader(file)
    with transaction.atomic():
        for row in reader:
            System.objects.create(
                name=row['name'],
                description=row['description'],
                owner=row['owner'],
            )