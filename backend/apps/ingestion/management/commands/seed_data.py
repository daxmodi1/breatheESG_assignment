"""
Management command to seed the database with sample data.
Creates: 1 tenant, 1 analyst user, and sample ingestions for all 3 sources.
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from apps.tenants.models import Tenant, TenantUser
from apps.ingestion.models import RawIngestion
from apps.emissions.models import EmissionRecord
from apps.ingestion.parsers.sap import parse_sap_file
from apps.ingestion.parsers.utility import parse_utility_file
from apps.ingestion.parsers.travel import parse_travel_file

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / 'sample_data'


class Command(BaseCommand):
    help = 'Seed the database with sample tenant, user, and ingestion data.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # 1. Create tenant
        tenant, _ = Tenant.objects.get_or_create(slug='acme-corp', defaults={'name': 'Acme Corporation'})
        self.stdout.write(f'  Tenant: {tenant}')

        # 2. Create analyst user
        user, created = User.objects.get_or_create(
            username='analyst',
            defaults={'email': 'analyst@acmecorp.com', 'first_name': 'Jane', 'last_name': 'Analyst'}
        )
        user.email = 'analyst@acmecorp.com'
        user.first_name = 'Jane'
        user.last_name = 'Analyst'
        user.set_password('analyst123')
        user.save()
        if created:
            self.stdout.write('  Created user: analyst / analyst123')
        else:
            self.stdout.write('  Updated user: analyst / analyst123')

        TenantUser.objects.update_or_create(user=user, defaults={'tenant': tenant, 'role': 'analyst'})

        # 3. Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@acmecorp.com', 'first_name': 'John', 'last_name': 'Admin',
                      'is_staff': True, 'is_superuser': True}
        )
        admin_user.email = 'admin@acmecorp.com'
        admin_user.first_name = 'John'
        admin_user.last_name = 'Admin'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('admin123')
        admin_user.save()
        if created:
            self.stdout.write('  Created admin: admin / admin123')
        else:
            self.stdout.write('  Updated admin: admin / admin123')

        TenantUser.objects.update_or_create(user=admin_user, defaults={'tenant': tenant, 'role': 'admin'})

        # 4. Ingest sample files
        samples = [
            ('sap_sample.txt', 'SAP', parse_sap_file),
            ('utility_sample.csv', 'UTILITY', parse_utility_file),
            ('travel_sample.csv', 'TRAVEL', parse_travel_file),
        ]

        for filename, source_type, parser in samples:
            if RawIngestion.objects.filter(tenant=tenant, source_type=source_type, filename=filename).exists():
                self.stdout.write(f'  [{source_type}] {filename}: already seeded')
                continue

            filepath = SAMPLE_DIR / filename
            if not filepath.exists():
                self.stdout.write(self.style.WARNING(f'  Skipping {filename}: file not found'))
                continue

            content = filepath.read_bytes()
            ingestion = RawIngestion.objects.create(
                tenant=tenant, source_type=source_type, uploaded_by=user,
                filename=filename, raw_file=ContentFile(content, name=filename),
            )

            result = parser(content, filename)
            records = []
            for rec in result['records']:
                records.append(EmissionRecord(
                    tenant=tenant, source_ingestion=ingestion,
                    source_row_index=rec['source_row_index'], source_row_raw=rec['source_row_raw'],
                    activity_date=rec['activity_date'], period_start=rec['period_start'],
                    period_end=rec['period_end'], scope=rec['scope'],
                    category=rec['category'], subcategory=rec.get('subcategory', ''),
                    quantity_raw=rec['quantity_raw'], unit_raw=rec['unit_raw'],
                    quantity_normalised=rec['quantity_normalised'],
                    unit_normalised=rec['unit_normalised'],
                    emission_factor=rec.get('emission_factor'),
                    emission_factor_source=rec.get('emission_factor_source', ''),
                    co2e_kg=rec.get('co2e_kg'), metadata=rec.get('metadata', {}),
                    is_anomaly=rec.get('is_anomaly', False),
                    anomaly_reason=rec.get('anomaly_reason', ''),
                    status='FLAGGED' if rec.get('is_anomaly') else 'PENDING',
                ))
            EmissionRecord.objects.bulk_create(records)

            ingestion.row_count = len(records)
            ingestion.parse_errors = result['errors']
            ingestion.status = 'DONE'
            ingestion.save()

            self.stdout.write(f'  [{source_type}] {filename}: {len(records)} records, {len(result["errors"])} errors')

        self.stdout.write(self.style.SUCCESS('Done! Login with analyst/analyst123 or admin/admin123'))
