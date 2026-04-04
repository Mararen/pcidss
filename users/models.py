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

class TipoSAQ(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class SeccionSAQ(models.Model):
    tipo = models.ForeignKey(TipoSAQ, related_name="secciones", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class PreguntaSAQ(models.Model):
    texto = models.TextField()
    referencia_pci = models.CharField(max_length=50, blank=True)

    tipos_saq = models.ManyToManyField(TipoSAQ, related_name="preguntas")

    def __str__(self):
        return self.texto


class PreguntaEnSeccion(models.Model):
    pregunta = models.ForeignKey(PreguntaSAQ, on_delete=models.CASCADE)
    seccion = models.ForeignKey(SeccionSAQ, related_name="preguntas", on_delete=models.CASCADE)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ["orden"]