from django.core.management.base import BaseCommand
from survey.models import Tenant, Employee
import csv
import pandas as pd

class Command(BaseCommand):
    help = 'Read Tenant Employees'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int, help='Indicates the tenant id')
        
    def handle(self, *args, **kwargs):
        tenant = Tenant.objects.get(id=kwargs["id"])
        
        if tenant:
            with open("survey/import/upload.csv") as f:
                data = csv.reader(f)              
                
            # data = pd.read_csv("survey/import/upload.csv", )
            
            # for i in data:
            #     print(i[1])
                
                Employee.objects.bulk_create(
                    [Employee(employee_id=emp[0],name=emp[1],email=emp[2],company=emp[3],
                                job_title=emp[4],section=emp[5],phone_number=emp[6],
                                division=emp[7],department=emp[8],tenant=tenant
                                )
                        for emp in data])
            
            self.stdout.write(f"Count: {tenant.employee_set.count()}")
            