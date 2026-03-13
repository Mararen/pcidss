from django.db import models
from django.contrib.auth.models import User

class Entidad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_empresa = models.CharField(max_length=150)
    dba = models.CharField(max_length=150)
    email = models.EmailField()
    sitio_web = models.URLField(blank=True, null=True)
    contacto = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_empresa