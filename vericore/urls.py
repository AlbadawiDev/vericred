from django.urls import path

from . import views

urlpatterns = [
    path('', views.certificate_list, name='certificate_list'),
    path('new/', views.certificate_create, name='certificate_create'),
    path('<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('<int:pk>/edit/', views.certificate_update, name='certificate_update'),
    path('<int:pk>/status/', views.certificate_status_update, name='certificate_status_update'),
    path('verify/<uuid:token>/', views.public_verify, name='public_verify'),
    path('audit/', views.audit_log_list, name='audit_log_list'),
]
