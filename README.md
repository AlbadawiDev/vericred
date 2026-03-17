# VeriCred - Digital Certificate Verification System

VeriCred is a Django-based web app for institutional certificate issuance and public verification using QR codes.

## Features

- Authentication (Django auth login/logout)
- Role-based authorization (`ADMIN`, `ISSUER`, `REVIEWER`, `VIEWER`)
- Certificate CRUD
- Workflow statuses and approval pipeline:
  - Draft
  - Pending Review
  - Approved
  - Rejected
  - Issued
  - Revoked
- QR generation per certificate
- Public verification endpoint using secure token
- Dashboard metrics
- Audit trail for creation/updates/workflow transitions
- Search and filtering for certificates and audit logs
- Revocation with mandatory reason

## Tech Stack

- Python 3.12+
- Django 5.x
- SQLite (default)
- `qrcode` + Pillow for QR image generation

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

## Role Configuration

Users are created through admin or shell and automatically get a `Profile` record.

Set user roles from Django admin:
- `/admin/vericore/profile/`

Suggested role mapping:
- `ISSUER`: create/edit drafts, submit, issue, revoke
- `REVIEWER`: approve/reject pending reviews
- `ADMIN`: full access
- `VIEWER`: read-only access

## Core Routes

- `/` Dashboard (authenticated)
- `/accounts/login/` Login
- `/certificates/` Certificate list + filtering
- `/certificates/new/` Create certificate
- `/certificates/<id>/` Detail + workflow controls
- `/certificates/verify/<token>/` Public verification page
- `/certificates/audit/` Audit logs

## Development & Tests

Run tests:

```bash
python manage.py test
```

## Notes

- QR code currently stores relative verify URL. In production you can switch to absolute URL generation.
- SQLite is used by default for easy local demos; PostgreSQL can be configured through Django settings for production.
