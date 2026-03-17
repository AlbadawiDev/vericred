# Generated manually for offline environment.
import django.db.models.deletion
import uuid
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('student_name', models.CharField(max_length=255)),
                ('student_email', models.EmailField(blank=True, max_length=254)),
                ('course_name', models.CharField(max_length=255)),
                ('institution_name', models.CharField(max_length=255)),
                ('issue_date', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Pending Review', 'Pending Review'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Issued', 'Issued'), ('Revoked', 'Revoked')], default='Draft', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('revocation_reason', models.TextField(blank=True)),
                ('verification_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('qr_code', models.ImageField(blank=True, upload_to='qr_codes/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='certificates_approved', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='certificates_created', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='certificates_reviewed', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('previous_status', models.CharField(blank=True, max_length=20)),
                ('new_status', models.CharField(blank=True, max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('certificate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='vericore.certificate')),
            ],
            options={'ordering': ['-timestamp']},
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('ISSUER', 'Issuer'), ('REVIEWER', 'Reviewer'), ('VIEWER', 'Viewer')], default='VIEWER', max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
