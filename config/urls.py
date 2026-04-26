import os
print("URLs cargadas desde:", os.path.abspath(__file__))

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('saq/', include(('saq.urls', 'saq'), namespace='saq')),
    path('tickets/', include('helpdesk.urls')),
]