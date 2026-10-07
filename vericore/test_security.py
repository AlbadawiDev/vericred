import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AuditLog, Certificate, CertificateStatus, UserRole


class SecurityRegressionTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp(prefix='vericred-test-')
        self.addCleanup(shutil.rmtree, self.media)
        self.settings = override_settings(MEDIA_ROOT=self.media, PUBLIC_BASE_URL='https://verify.example.com')
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        User = get_user_model()
        self.issuer = User.objects.create_user('issuer')
        self.issuer.profile.role = UserRole.ISSUER
        self.issuer.profile.save()
        self.reviewer = User.objects.create_user('reviewer')
        self.reviewer.profile.role = UserRole.REVIEWER
        self.reviewer.profile.save()
        self.viewer = User.objects.create_user('viewer')
        self.other_issuer = User.objects.create_user('other-issuer')
        self.other_issuer.profile.role = UserRole.ISSUER
        self.other_issuer.profile.save()
        self.cert = Certificate.objects.create(student_name='Synthetic Example', course_name='Testing',
                                               institution_name='Demo Academy', created_by=self.issuer)

    def transition(self, user, status):
        self.client.force_login(user)
        return self.client.post(reverse('certificate_status_update', kwargs={'pk': self.cert.pk}),
                                {'status': status, 'notes': 'Synthetic audit note'})

    def test_viewer_cannot_reset_rejected_certificate(self):
        self.cert.status = CertificateStatus.REJECTED
        self.cert.save()
        self.assertEqual(self.transition(self.viewer, CertificateStatus.DRAFT).status_code, 403)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, CertificateStatus.REJECTED)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_issuer_cannot_modify_another_issuers_draft(self):
        self.client.force_login(self.other_issuer)
        response = self.client.get(reverse('certificate_update', kwargs={'pk': self.cert.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.transition(self.other_issuer, CertificateStatus.PENDING_REVIEW).status_code, 403)

    def test_approval_retains_actual_reviewer_when_issued(self):
        self.cert.status = CertificateStatus.PENDING_REVIEW
        self.cert.save()
        self.transition(self.reviewer, CertificateStatus.APPROVED)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.approved_by, self.reviewer)
        self.transition(self.issuer, CertificateStatus.ISSUED)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.approved_by, self.reviewer)

    def test_draft_is_not_publicly_visible(self):
        response = self.client.get(self.cert.get_public_verify_url())
        self.assertEqual(response.status_code, 404)

    def test_qr_encodes_a_scannable_absolute_url(self):
        with patch('vericore.models.qrcode.QRCode') as qr:
            qr.return_value.make_image.return_value.save.side_effect = lambda buffer, **kw: buffer.write(b'PNG')
            Certificate.objects.create(student_name='Synthetic QR', course_name='Testing',
                                       institution_name='Demo Academy', created_by=self.issuer)
            self.assertTrue(qr.return_value.add_data.call_args[0][0].startswith('https://verify.example.com/certificates/verify/'))

    def test_audit_failure_rolls_back_workflow(self):
        with patch('vericore.views.AuditLog.objects.create', side_effect=RuntimeError('Synthetic failure')):
            with self.assertRaises(RuntimeError):
                self.transition(self.issuer, CertificateStatus.PENDING_REVIEW)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, CertificateStatus.DRAFT)

    def test_csrf_is_required_for_workflow(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.issuer)
        response = client.post(reverse('certificate_status_update', kwargs={'pk': self.cert.pk}),
                               {'status': CertificateStatus.PENDING_REVIEW})
        self.assertEqual(response.status_code, 403)

    def test_unknown_verification_token_returns_404(self):
        response = self.client.get(reverse('public_verify', kwargs={'token': '00000000-0000-0000-0000-000000000001'}))
        self.assertEqual(response.status_code, 404)
