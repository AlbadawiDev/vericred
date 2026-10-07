from django.contrib import admin

from .models import AuditLog, Certificate, Profile


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'course_name', 'institution_name', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'institution_name', 'issue_date')
    search_fields = ('student_name', 'course_name', 'certificate_id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('certificate', 'actor', 'action', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('action', 'new_status')
    search_fields = ('certificate__student_name', 'actor__username')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
