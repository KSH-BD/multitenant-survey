from django.core.management.base import BaseCommand
from survey.models import Tenant, Employee
import csv

class Command(BaseCommand):
    help = 'Read Tenant Employees'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int, help='Indicates the tenant id')
        
    def handle(self, *args, **kwargs):
        tenant = Tenant.objects.get(id=kwargs["id"])
        
        if tenant:
            with open("survey/import/fm.csv") as f:
                data = csv.reader(f)              
                
                Employee.objects.bulk_create(
                    [Employee(employee_id=emp[0],name=emp[1],email=emp[2],company=emp[3],
                              job_title=emp[4],section=emp[5],phone_number=emp[6],tenant=tenant
                              )
                     for emp in data])
                
                self.stdout.write(f"Count: {tenant.employee_set.count()}")
            