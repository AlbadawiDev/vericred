"""Prepare only synthetic local data and a locally generated demo password."""
import json
import os
from pathlib import Path
import secrets
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vericred.settings')
os.environ['DEBUG'] = '1'
os.environ['DEMO_PASSWORD'] = secrets.token_urlsafe(24)

import django
django.setup()
from django.core.management import call_command
from vericore.models import Certificate, CertificateStatus

call_command('migrate', verbosity=0)
call_command('seed_demo')
credentials = BASE / '.demo-credentials.json'
credentials.write_text(json.dumps({'username': 'demo-issuer', 'reviewer': 'demo-reviewer',
                                  'viewer': 'demo-viewer', 'password': os.environ['DEMO_PASSWORD']}, indent=2), encoding='utf-8')
public = Certificate.objects.filter(status=CertificateStatus.ISSUED, institution_name='Demo Academy').first()
print(f'Public synthetic verification: {public.get_absolute_verify_url()}')
print('Credentials saved locally in .demo-credentials.json (excluded from Git).')
