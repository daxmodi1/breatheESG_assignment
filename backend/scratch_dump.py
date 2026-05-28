import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breathe_esg.settings.dev')
django.setup()

from apps.emissions.models import EmissionRecord
from django.db.models import Sum

for i in [1, 2, 3]:
    total = EmissionRecord.objects.filter(scope=i).aggregate(Sum('co2e_kg'))['co2e_kg__sum']
    print(f"Scope {i}: {total}")
