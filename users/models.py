from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

# ─── CONFIGURACIÓN GENERAL ───────────────────────────────

class ConfiguracionGeneral(models.Model):
    nombre_sistema = models.CharField(max_length=150)
    tiempo_sesion = models.IntegerField()
    idioma = models.CharField(max_length=20, default="es")
    zona_horaria = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Configuración General"


# ─── SEGURIDAD ───────────────────────────────────────────

class PoliticaSeguridad(models.Model):
    longitud_minima = models.IntegerField(default=8)
    requiere_numeros = models.BooleanField(default=True)
    requiere_mayusculas = models.BooleanField(default=True)
    requiere_simbolos = models.BooleanField(default=True)
    dias_vigencia = models.IntegerField()
    intentos_fallidos = models.IntegerField()
    actualizado_en = models.DateTimeField(auto_now=True)


# ─── NOTIFICACIONES ──────────────────────────────────────

class NotificacionConfig(models.Model):
    TIPOS = [("alerta", "Alerta"), ("recordatorio", "Recordatorio")]
    CANALES = [("correo", "Correo"), ("sistema", "Sistema")]

    tipo = models.CharField(max_length=20, choices=TIPOS, unique=True)
    dias_antes = models.IntegerField()
    canal = models.CharField(max_length=20, choices=CANALES)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)


# ─── PERMISOS ────────────────────────────────────────────

class PermisosSistema(models.Model):
    class Meta:
        permissions = [
            ("ver_dashboard",            "Puede ver dashboard"),
            ("ver_usuarios",             "Puede ver usuarios"),
            ("gestionar_usuarios",       "Puede gestionar usuarios"),
            ("ver_entidades",            "Puede ver entidades"),
            ("gestionar_entidades",      "Puede gestionar entidades"),
            ("ver_evidencias",           "Puede ver evidencias"),
            ("gestionar_renovacion",     "Puede gestionar renovación"),
            ("gestionar_configuracion",  "Puede gestionar configuración"),
        ]

# ─────────────────────────────────────────────
# AUDITORÍA
# ─────────────────────────────────────────────

class LogAuditoria(models.Model):
    ACCIONES = [
        ("LOGIN", "Inicio de sesión"),
        ("LOGOUT", "Cierre de sesión"),
        ("CREATE", "Creación"),
        ("UPDATE", "Actualización"),
        ("DELETE", "Eliminación"),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_events_as_actor"
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_as_target"
    )

    accion = models.CharField(max_length=20, choices=ACCIONES)
    modulo = models.CharField(max_length=50)
    descripcion = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.modulo}"


# ─────────────────────────────────────────────
# ENTIDADES
# ─────────────────────────────────────────────

class Entidad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre_empresa = models.CharField(max_length=150)
    dba = models.CharField(max_length=150)
    email = models.EmailField()
    sitio_web = models.URLField(blank=True, null=True)
    contacto = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    creado_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    related_name="entidades_creadas"
    )

    modificado_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    related_name="entidades_modificadas"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_empresa




