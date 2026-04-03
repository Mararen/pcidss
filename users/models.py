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
    """SAQ A, SAQ B, SAQ C, SAQ D, SAQ A-EP, SAQ B-IP"""
    nombre      = models.CharField(max_length=50, unique=True)   # "SAQ A"
    codigo      = models.SlugField(max_length=20, unique=True)   # "saq-a"
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Tipo de SAQ"
        verbose_name_plural = "Tipos de SAQ"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class SeccionSAQ(models.Model):
    """Part 1a, Part 2, Part 3..."""
    tipo_saq    = models.ForeignKey(TipoSAQ, on_delete=models.CASCADE, related_name="secciones")
    nombre      = models.CharField(max_length=100)   # "Part 1a. Comercio Evaluado"
    orden       = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Sección SAQ"
        verbose_name_plural = "Secciones SAQ"
        ordering = ["orden"]

    def __str__(self):
        return f"{self.tipo_saq} — {self.nombre}"


class PreguntaSAQ(models.Model):
    """
    Pregunta reutilizable entre secciones.
    Una misma pregunta puede aparecer en varias secciones de distintos SAQ.
    """
    TIPO_RESPUESTA = [
        ("si_no_na", "Sí / No / N/A"),
    ]

    secciones       = models.ManyToManyField(
                        SeccionSAQ,
                        through="PreguntaEnSeccion",
                        related_name="preguntas"
                      )
    texto           = models.TextField()
    tipo_respuesta  = models.CharField(max_length=20, choices=TIPO_RESPUESTA, default="si_no_na")
    referencia_pci  = models.CharField(max_length=50, blank=True)  # ej. "Req. 2.1"
    activa          = models.BooleanField(default=True)
    fecha_creacion  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pregunta SAQ"
        verbose_name_plural = "Preguntas SAQ"
        ordering = ["id"]

    def __str__(self):
        return f"[{self.referencia_pci}] {self.texto[:60]}"


class PreguntaEnSeccion(models.Model):
    """Tabla intermedia que define el orden de cada pregunta dentro de una sección."""
    pregunta = models.ForeignKey(PreguntaSAQ, on_delete=models.CASCADE)
    seccion  = models.ForeignKey(SeccionSAQ, on_delete=models.CASCADE)
    orden    = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Pregunta en sección"
        verbose_name_plural = "Preguntas en sección"
        ordering = ["orden"]
        unique_together = [("pregunta", "seccion")]

    def __str__(self):
        return f"{self.seccion} — {self.pregunta}"
