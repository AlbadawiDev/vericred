from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from vericore import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('certificates/', include('vericore.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
