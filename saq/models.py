from django.db import models
from django.conf import settings


class Requisito(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.TextField()

    def _str_(self):
        return self.codigo


class SAQ(models.Model):
    codigo = models.CharField(max_length=10, unique=True)

    def _str_(self):
        return self.codigo


class PreguntaSAQ(models.Model):
    requisito = models.ForeignKey(Requisito, on_delete=models.CASCADE)
    texto = models.TextField()
    tipo_respuesta = models.CharField(max_length=30, default="SI/NO")
    saqs = models.ManyToManyField(SAQ)

    def _str_(self):
        return self.texto[:80]


class Evaluacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, default="EN_PROCESO")