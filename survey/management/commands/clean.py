from django.core.management.base import BaseCommand
from survey.models import Tenant, Employee
import csv

class Command(BaseCommand):
    help = 'Read Tenant Employees'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int, help='Indicates the tenant id')
        
    def handle(self, *args, **kwargs):
        tenant = Tenant.objects.get(id=kwargs["id"])        
        tenant.employee_set.all().delete()
        self.stdout.write(f"Count: {tenant.employee_set.count()}")
            