from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog, Certificate, CertificateStatus, UserRole


User = get_user_model()


class CertificateWorkflowTests(TestCase):
    def setUp(self):
        self.issuer = User.objects.create_user(username='issuer', password='pass12345')
        self.reviewer = User.objects.create_user(username='reviewer', password='pass12345')
        self.issuer.profile.role = UserRole.ISSUER
        self.issuer.profile.save()
        self.reviewer.profile.role = UserRole.REVIEWER
        self.reviewer.profile.save()

    def test_end_to_end_workflow_and_public_verification(self):
        self.client.login(username='issuer', password='pass12345')
        create_resp = self.client.post(
            reverse('certificate_create'),
            {
                'student_name': 'Alice Example',
                'student_email': 'alice@example.com',
                'course_name': 'Advanced Cryptography',
                'institution_name': 'Veri University',
                'issue_date': '2026-01-01',
                'description': 'Top student',
            },
            follow=True,
        )
        self.assertEqual(create_resp.status_code, 200)
        cert = Certificate.objects.get(student_name='Alice Example')
        self.assertTrue(cert.qr_code.name)

        self.client.post(reverse('certificate_status_update', kwargs={'pk': cert.pk}), {'status': CertificateStatus.PENDING_REVIEW, 'notes': 'Ready'})
        cert.refresh_from_db()
        self.assertEqual(cert.status, CertificateStatus.PENDING_REVIEW)

        self.client.logout()
        self.client.login(username='reviewer', password='pass12345')
        self.client.post(reverse('certificate_status_update', kwargs={'pk': cert.pk}), {'status': CertificateStatus.APPROVED, 'notes': 'Approved by committee'})
        cert.refresh_from_db()
        self.assertEqual(cert.status, CertificateStatus.APPROVED)

        self.client.logout()
        self.client.login(username='issuer', password='pass12345')
        self.client.post(reverse('certificate_status_update', kwargs={'pk': cert.pk}), {'status': CertificateStatus.ISSUED, 'notes': 'Issued'})
        cert.refresh_from_db()
        self.assertEqual(cert.status, CertificateStatus.ISSUED)

        verify_resp = self.client.get(reverse('public_verify', kwargs={'token': cert.verification_token}))
        self.assertContains(verify_resp, 'valid and currently issued')

    def test_issuer_cannot_approve(self):
        cert = Certificate.objects.create(
            student_name='Bob',
            course_name='Data Science',
            institution_name='Veri University',
            created_by=self.issuer,
            status=CertificateStatus.PENDING_REVIEW,
        )
        self.client.login(username='issuer', password='pass12345')
        resp = self.client.post(reverse('certificate_status_update', kwargs={'pk': cert.pk}), {'status': CertificateStatus.APPROVED})
        self.assertEqual(resp.status_code, 403)

    def test_revocation_requires_reason(self):
        cert = Certificate.objects.create(
            student_name='Charlie',
            course_name='ML',
            institution_name='Veri University',
            created_by=self.issuer,
            status=CertificateStatus.ISSUED,
        )
        self.client.login(username='issuer', password='pass12345')
        self.client.post(reverse('certificate_status_update', kwargs={'pk': cert.pk}), {'status': CertificateStatus.REVOKED})
        cert.refresh_from_db()
        self.assertEqual(cert.status, CertificateStatus.ISSUED)


class AuditLogTests(TestCase):
    def test_log_created_on_create(self):
        user = User.objects.create_user(username='creator', password='pass12345')
        user.profile.role = UserRole.ISSUER
        user.profile.save()
        self.client.login(username='creator', password='pass12345')
        self.client.post(
            reverse('certificate_create'),
            {
                'student_name': 'Dana',
                'student_email': 'dana@example.com',
                'course_name': 'Networks',
                'institution_name': 'Veri University',
                'issue_date': '2026-01-01',
            },
        )
        self.assertEqual(AuditLog.objects.count(), 1)
