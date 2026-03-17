import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone


class CertificateStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    PENDING_REVIEW = 'Pending Review', 'Pending Review'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'
    ISSUED = 'Issued', 'Issued'
    REVOKED = 'Revoked', 'Revoked'


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    ISSUER = 'ISSUER', 'Issuer'
    REVIEWER = 'REVIEWER', 'Reviewer'
    VIEWER = 'VIEWER', 'Viewer'


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VIEWER)

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Certificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student_name = models.CharField(max_length=255)
    student_email = models.EmailField(blank=True)
    course_name = models.CharField(max_length=255)
    institution_name = models.CharField(max_length=255)
    issue_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=CertificateStatus.choices, default=CertificateStatus.DRAFT)
    description = models.TextField(blank=True)
    revocation_reason = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='certificates_created')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='certificates_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='certificates_approved')

    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student_name} - {self.course_name}'

    def get_public_verify_url(self):
        return reverse('public_verify', kwargs={'token': self.verification_token})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(self.get_public_verify_url())
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr-{self.certificate_id}.png'
            self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
            super().save(update_fields=['qr_code'])


class AuditLog(models.Model):
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=255)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.certificate_id} - {self.action}'
