from django import forms

from .models import Certificate, CertificateStatus


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = [
            'student_name',
            'student_email',
            'course_name',
            'institution_name',
            'issue_date',
            'description',
        ]


class StatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=CertificateStatus.choices)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    revocation_reason = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        reason = cleaned.get('revocation_reason')
        if status == CertificateStatus.REVOKED and not reason:
            self.add_error('revocation_reason', 'Revocation reason is required.')
        return cleaned
