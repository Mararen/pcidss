from django.db import models
from django.contrib.auth.models import User


# ─── PERMISOS DEL SISTEMA ────────────────────────────────

class PermisosSistema(models.Model):
    class Meta:
        permissions = [
            ("ver_dashboard", "Puede ver dashboard"),

            ("ver_usuarios", "Puede ver usuarios"),
            ("gestionar_usuarios", "Puede gestionar usuarios"),

            ("ver_entidades", "Puede ver entidades"),
            ("gestionar_entidades", "Puede gestionar entidades"),

            ("ver_saq", "Puede ver SAQ"),
            ("editar_saq", "Puede editar SAQ"),

            ("usar_pretest", "Puede usar PreTest"),

            ("ver_evidencias", "Puede ver evidencias"),

            ("gestionar_renovacion", "Puede gestionar renovación"),
        ]


# ─── ENTIDADES ───────────────────────────────────────────

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


# ─── SAQ ─────────────────────────────────────────────────

class TipoSAQ(models.Model):
    nombre = models.CharField(max_length=100)

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

    def __str__(self):
        return self.texto


class PreguntaEnSeccion(models.Model):
    pregunta = models.ForeignKey(PreguntaSAQ, on_delete=models.CASCADE)
    seccion = models.ForeignKey(SeccionSAQ, related_name="preguntas", on_delete=models.CASCADE)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ["orden"]


class RespuestaSAQ(models.Model):
    OPCIONES = [
        ("SI", "Sí"),
        ("NO", "No"),
        ("NA", "No aplica"),
    ]

    entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(PreguntaSAQ, on_delete=models.CASCADE)
    respuesta = models.CharField(max_length=2, choices=OPCIONES)
    comentario = models.TextField(blank=True)

    class Meta:
        unique_together = ("entidad", "pregunta")


# ─── PRETEST ─────────────────────────────────────────────

class PreguntaPreTest(models.Model):
    numero = models.IntegerField(default=0)
    saq_destino = models.CharField(max_length=20, default='')
    texto_es = models.TextField()
    texto_en = models.TextField(blank=True, default='')
    version_pci = models.CharField(max_length=10, default='4.0.1')


class RespuestaPreTest(models.Model):
    OPCIONES = [("SI", "Sí"), ("NO", "No")]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(PreguntaPreTest, on_delete=models.CASCADE)
    respuesta = models.CharField(max_length=2, choices=OPCIONES)

    class Meta:
        unique_together = ("usuario", "pregunta")