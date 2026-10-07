"""Explicit, synthetic demo seeding; never imports an institutional database."""
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from vericore.models import AuditLog, Certificate, CertificateStatus, UserRole


class Command(BaseCommand):
    help = 'Create synthetic local demo accounts and four workflow examples (DEMO_PASSWORD required).'

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD', '')
        if not settings.DEBUG:
            raise CommandError('Demo seeding is permitted only with DEBUG=1.')
        if len(password) < 12:
            raise CommandError('Set DEMO_PASSWORD to a unique local password with at least 12 characters.')
        users = {}
        for name, role in [('demo-issuer', UserRole.ISSUER), ('demo-reviewer', UserRole.REVIEWER), ('demo-viewer', UserRole.VIEWER)]:
            user, created = get_user_model().objects.get_or_create(username=name)
            if not created and user.profile.role != role:
                raise CommandError(f'Existing account {name} has a different role; no changes were made.')
            user.set_password(password)
            user.save()
            user.profile.role = role
            user.profile.save()
            users[role] = user
        for index, status in enumerate([CertificateStatus.DRAFT, CertificateStatus.PENDING_REVIEW, CertificateStatus.ISSUED, CertificateStatus.REVOKED], 1):
            cert, created = Certificate.objects.get_or_create(
                student_name=f'Synthetic Learner {index}', course_name='Applied Software Engineering',
                institution_name='Demo Academy', created_by=users[UserRole.ISSUER],
                defaults={'status': status, 'student_email': f'learner{index}@example.com',
                          'description': 'Synthetic portfolio sample; no institutional data.'},
            )
            if created:
                if status in [CertificateStatus.ISSUED, CertificateStatus.REVOKED]:
                    cert.approved_by = users[UserRole.REVIEWER]
                    cert.reviewed_by = users[UserRole.REVIEWER]
                    if status == CertificateStatus.REVOKED:
                        cert.revocation_reason = 'Synthetic example: superseded by a corrected certificate.'
                    cert.save()
                AuditLog.objects.create(certificate=cert, actor=users[UserRole.ISSUER],
                                        action='Synthetic demo fixture', new_status=status)
        self.stdout.write(self.style.SUCCESS('Synthetic demo ready: 3 accounts, 4 certificates. Password not logged.'))
