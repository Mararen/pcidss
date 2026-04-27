from django.db import models

# ─────────────────────────────────────────────
# CATÁLOGOS
# ─────────────────────────────────────────────

class TipoEntidad(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("gestionar_catalogos", "Puede gestionar catálogos")]

    def __str__(self): return self.nombre


class Pais(models.Model):
    nombre    = models.CharField(max_length=100, unique=True)
    codigo    = models.CharField(max_length=3, unique=True)
    activo    = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class TipoContrato(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class NivelRiesgo(models.Model):
    NIVELES = [
        ("bajo",    "Bajo"),
        ("medio",   "Medio"),
        ("alto",    "Alto"),
        ("critico", "Crítico"),
    ]
    nombre      = models.CharField(max_length=50, unique=True)
    nivel       = models.CharField(max_length=10, choices=NIVELES)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class TipoSAQ(models.Model):
    codigo      = models.CharField(max_length=20, unique=True)
    nombre      = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.codigo


class TipoDocumento(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class EstadoCertificacion(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class TipoRol(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre


class Idioma(models.Model):
    nombre    = models.CharField(max_length=100, unique=True)
    codigo    = models.CharField(max_length=10, unique=True)
    activo    = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nombre