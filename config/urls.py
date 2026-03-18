import os
print("URLs cargadas desde:", os.path.abspath(__file__))  # eliminar en producción

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
]