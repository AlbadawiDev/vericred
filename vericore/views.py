from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CertificateForm, StatusUpdateForm
from .models import AuditLog, Certificate, CertificateStatus
from .permissions import can_edit_certificate, can_issue, can_review, get_user_role


TRANSITIONS = {
    CertificateStatus.DRAFT: [CertificateStatus.PENDING_REVIEW],
    CertificateStatus.PENDING_REVIEW: [CertificateStatus.APPROVED, CertificateStatus.REJECTED],
    CertificateStatus.REJECTED: [CertificateStatus.DRAFT],
    CertificateStatus.APPROVED: [CertificateStatus.ISSUED],
    CertificateStatus.ISSUED: [CertificateStatus.REVOKED],
}


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    context = {
        'role': role,
        'total_certificates': Certificate.objects.count(),
        'pending_reviews': Certificate.objects.filter(status=CertificateStatus.PENDING_REVIEW).count(),
        'issued_count': Certificate.objects.filter(status=CertificateStatus.ISSUED).count(),
        'revoked_count': Certificate.objects.filter(status=CertificateStatus.REVOKED).count(),
        'recent_certificates': Certificate.objects.select_related('created_by')[:5],
    }
    return render(request, 'vericore/dashboard.html', context)


@login_required
def certificate_list(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '')

    certificates = Certificate.objects.select_related('created_by', 'reviewed_by', 'approved_by').all()
    if status:
        certificates = certificates.filter(status=status)
    if query:
        certificates = certificates.filter(
            Q(student_name__icontains=query)
            | Q(course_name__icontains=query)
            | Q(institution_name__icontains=query)
            | Q(certificate_id__icontains=query)
        )

    return render(
        request,
        'vericore/certificate_list.html',
        {
            'certificates': certificates,
            'status_choices': CertificateStatus.choices,
            'selected_status': status,
            'query': query,
        },
    )


@login_required
def certificate_create(request):
    if not can_issue(request.user):
        return HttpResponseForbidden('Not allowed')

    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.created_by = request.user
            cert.save()
            AuditLog.objects.create(
                certificate=cert,
                actor=request.user,
                action='Created certificate',
                new_status=cert.status,
            )
            messages.success(request, 'Certificate created successfully.')
            return redirect('certificate_detail', pk=cert.pk)
    else:
        form = CertificateForm()

    return render(request, 'vericore/certificate_form.html', {'form': form, 'is_edit': False})


@login_required
def certificate_update(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    if not can_edit_certificate(request.user, certificate):
        return HttpResponseForbidden('Cannot edit in current state or role.')

    if request.method == 'POST':
        form = CertificateForm(request.POST, instance=certificate)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                certificate=certificate,
                actor=request.user,
                action='Updated certificate metadata',
                previous_status=certificate.status,
                new_status=certificate.status,
            )
            messages.success(request, 'Certificate updated successfully.')
            return redirect('certificate_detail', pk=certificate.pk)
    else:
        form = CertificateForm(instance=certificate)
    return render(request, 'vericore/certificate_form.html', {'form': form, 'is_edit': True, 'certificate': certificate})


@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(Certificate.objects.select_related('created_by', 'reviewed_by', 'approved_by'), pk=pk)
    return render(request, 'vericore/certificate_detail.html', {'certificate': certificate, 'status_form': StatusUpdateForm(initial={'status': certificate.status})})


@login_required
def certificate_status_update(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.method != 'POST':
        return redirect('certificate_detail', pk=pk)

    form = StatusUpdateForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Invalid workflow update request.')
        return redirect('certificate_detail', pk=pk)

    new_status = form.cleaned_data['status']
    notes = form.cleaned_data['notes']
    reason = form.cleaned_data.get('revocation_reason', '')

    if new_status == certificate.status:
        messages.info(request, 'No status change made.')
        return redirect('certificate_detail', pk=pk)

    allowed_next = TRANSITIONS.get(certificate.status, [])
    if new_status not in allowed_next:
        messages.error(request, f'Invalid transition from {certificate.status} to {new_status}.')
        return redirect('certificate_detail', pk=pk)

    if new_status in [CertificateStatus.APPROVED, CertificateStatus.REJECTED] and not can_review(request.user):
        return HttpResponseForbidden('Reviewer role required.')

    if new_status in [CertificateStatus.PENDING_REVIEW, CertificateStatus.ISSUED, CertificateStatus.REVOKED] and not can_issue(request.user):
        return HttpResponseForbidden('Issuer role required.')

    old_status = certificate.status
    certificate.status = new_status
    if new_status in [CertificateStatus.APPROVED, CertificateStatus.REJECTED]:
        certificate.reviewed_by = request.user
    if new_status == CertificateStatus.ISSUED:
        certificate.approved_by = request.user
    if new_status == CertificateStatus.REVOKED:
        certificate.revocation_reason = reason
    certificate.save()

    AuditLog.objects.create(
        certificate=certificate,
        actor=request.user,
        action='Workflow transition',
        previous_status=old_status,
        new_status=new_status,
        notes=notes or reason,
    )

    messages.success(request, f'Certificate status updated to {new_status}.')
    return redirect('certificate_detail', pk=pk)


def public_verify(request, token):
    certificate = get_object_or_404(Certificate, verification_token=token)
    is_valid = certificate.status == CertificateStatus.ISSUED
    return render(request, 'vericore/public_verify.html', {'certificate': certificate, 'is_valid': is_valid})


@login_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('certificate', 'actor')
    certificate_id = request.GET.get('certificate_id', '')
    if certificate_id:
        logs = logs.filter(certificate__certificate_id__icontains=certificate_id)
    return render(request, 'vericore/audit_logs.html', {'logs': logs, 'certificate_id': certificate_id})
