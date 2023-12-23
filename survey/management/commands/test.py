from django.core.management.base import BaseCommand
from survey.models import Tenant, Employee,Answer,Form
import csv
import random
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Read Tenant Employees'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int, help='Indicates the tenant id')
        
    def handle(self, *args, **kwargs):
        tenant = Tenant.objects.get(id=kwargs["id"])        
        form = tenant.form_set.first()
        for emp in tenant.employee_set.all():
            for q in tenant.question_set.all():
                    if q.text == "Latitude":
                        Answer.objects.create(form=form,employee=emp,question=q,answer=str(fake.latitude()))
                    
                    elif q.text == "Longitude":  
                        Answer.objects.create(form=form,employee=emp,question=q,answer=str(fake.longitude()))                        
                        
                    elif q.type in ["Radio","List"]:            
                        if q.questionoption_set.count() > 0:
                            r = random.choice(q.questionoption_set.all())
                            Answer.objects.create(form=form,employee=emp,question=q,answer=r.value)
                        else:
                            Answer.objects.create(form=form,employee=emp,question=q,answer="")
                                                    
                    else:
                        Answer.objects.create(form=form,employee=emp,question=q,answer=fake.text())
        self.stdout.write(f"{form.answer_set.count()}")

            