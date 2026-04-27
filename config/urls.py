import os

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalogos import views as catalogos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('saq/', include(('saq.urls', 'saq'), namespace='saq')),
    path('catalogos/', include(('catalogos.urls', 'catalogos'), namespace='catalogos')),

    path('tickets/', include('helpdesk.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)