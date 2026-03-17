from .models import UserRole


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserRole.ADMIN
    return getattr(getattr(user, 'profile', None), 'role', UserRole.VIEWER)


def can_edit_certificate(user, certificate):
    role = get_user_role(user)
    return role in [UserRole.ADMIN, UserRole.ISSUER] and certificate.status in ['Draft', 'Rejected']


def can_review(user):
    return get_user_role(user) in [UserRole.ADMIN, UserRole.REVIEWER]


def can_issue(user):
    return get_user_role(user) in [UserRole.ADMIN, UserRole.ISSUER]
