from .models import CertificateStatus, UserRole


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserRole.ADMIN
    return getattr(getattr(user, 'profile', None), 'role', UserRole.VIEWER)


def can_edit_certificate(user, certificate):
    return can_manage_certificate(user, certificate) and certificate.status in [CertificateStatus.DRAFT, CertificateStatus.REJECTED]


def can_manage_certificate(user, certificate):
    role = get_user_role(user)
    return role == UserRole.ADMIN or (role == UserRole.ISSUER and certificate.created_by_id == user.pk)


def can_review(user):
    return get_user_role(user) in [UserRole.ADMIN, UserRole.REVIEWER]


def can_issue(user):
    return get_user_role(user) in [UserRole.ADMIN, UserRole.ISSUER]
