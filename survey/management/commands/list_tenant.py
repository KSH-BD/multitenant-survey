from django.core.management.base import BaseCommand
from django.utils import timezone
from survey.models import Tenant

class Command(BaseCommand):
    help = 'List all tenants'

    def handle(self, *args, **kwargs):        
        for tenant in Tenant.objects.all():
            self.stdout.write(f"{tenant.id}- {tenant.name}")