from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────

class ConfiguracionGeneral(models.Model):
    nombre_sistema = models.CharField(max_length=150)
    tiempo_sesion = models.IntegerField()
    idioma = models.CharField(max_length=20, default="es")
    zona_horaria = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Configuración General"


# ─────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────

class PoliticaSeguridad(models.Model):
    longitud_minima     = models.IntegerField(default=8)
    requiere_numeros    = models.BooleanField(default=True)
    requiere_mayusculas = models.BooleanField(default=True)
    requiere_simbolos   = models.BooleanField(default=True)
    dias_vigencia       = models.IntegerField(default=90)   
    intentos_fallidos   = models.IntegerField(default=5)   
    actualizado_en      = models.DateTimeField(auto_now=True)


# ─────────────────────────────────────────────
# PERFIL DE SEGURIDAD
# ─────────────────────────────────────────────

from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilSeguridad(models.Model):
    usuario           = models.OneToOneField(
                          User, on_delete=models.CASCADE,
                          related_name="perfil_seguridad"
                        )
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta   = models.DateTimeField(null=True, blank=True)
    ultimo_intento    = models.DateTimeField(null=True, blank=True)
    ultimo_login_ok   = models.DateTimeField(null=True, blank=True)
    contrasena_desde  = models.DateTimeField(default=timezone.now)
    forzar_cambio     = models.BooleanField(default=False)

    def esta_bloqueado(self):
        if not self.bloqueado_hasta:
            return False
        if timezone.now() < self.bloqueado_hasta:
            return True
        self.bloqueado_hasta   = None
        self.intentos_fallidos = 0
        self.save(update_fields=["bloqueado_hasta", "intentos_fallidos"])
        return False

    def segundos_restantes(self):
        if self.bloqueado_hasta:
            return max(int((self.bloqueado_hasta - timezone.now()).total_seconds()), 0)
        return 0

    def registrar_intento_fallido(self, minutos_bloqueo=30):
        politica     = PoliticaSeguridad.objects.first()
        max_intentos = politica.intentos_fallidos if politica else 5
        self.intentos_fallidos += 1
        self.ultimo_intento     = timezone.now()
        if self.intentos_fallidos >= max_intentos:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=minutos_bloqueo)
        self.save(update_fields=["intentos_fallidos", "ultimo_intento", "bloqueado_hasta"])

    def resetear_intentos(self):
        self.intentos_fallidos = 0
        self.bloqueado_hasta   = None
        self.ultimo_login_ok   = timezone.now()
        self.save(update_fields=["intentos_fallidos", "bloqueado_hasta", "ultimo_login_ok"])

    def contrasena_vencida(self):
        politica = PoliticaSeguridad.objects.first()
        if not politica:
            return False
        return timezone.now() > (self.contrasena_desde + timedelta(days=politica.dias_vigencia))

    def __str__(self):
        return f"Seguridad: {self.usuario.username}"


@receiver(post_save, sender=User)
def crear_perfil_seguridad(sender, instance, created, **kwargs):
    if created:
        PerfilSeguridad.objects.get_or_create(usuario=instance)
        
# ─────────────────────────────────────────────
# NOTIFICACIONES
# ─────────────────────────────────────────────

class NotificacionConfig(models.Model):
    TIPOS = [
        ("vencimiento_certificacion", "Vencimiento de certificación"),
        ("vencimiento_contrato",      "Vencimiento de contrato"),
        ("pretest_pendiente",         "PreTest pendiente"),
        ("renovacion_proxima",        "Renovación próxima"),
    ]
    CANALES = [
        ("correo",  "Correo"),
        ("sistema", "Sistema"),
    ]
    ESTILOS = [
        ("info",    "Información"),
        ("warning", "Advertencia"),
        ("danger",  "Urgente"),
        ("success", "Éxito"),
    ]

    tipo      = models.CharField(max_length=40, choices=TIPOS, unique=True)
    dias_antes = models.IntegerField()
    canal     = models.CharField(max_length=20, choices=CANALES)
    estilo    = models.CharField(max_length=20, choices=ESTILOS, default="info")
    activo    = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

# ─────────────────────────────────────────────
# PERMISOS
# ─────────────────────────────────────────────

class PermisosSistema(models.Model):
    class Meta:
        permissions = [
            ("ver_dashboard",            "Puede ver dashboard"),
            ("ver_usuarios",             "Puede ver usuarios"),
            ("gestionar_usuarios",       "Puede gestionar usuarios"),
            ("ver_entidades",            "Puede ver entidades"),
            ("gestionar_entidades",      "Puede gestionar entidades"),
            ("ver_evidencias",           "Puede ver evidencias"),
            ("gestionar_evidencias",     "Puede gestionar evidencias"),
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
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    nombre_empresa = models.CharField(
        max_length=100,
        unique=True
    )

    dba = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    sitio_web = models.URLField(
        blank=True,
        null=True
    )

    contacto = models.CharField(
        max_length=100
    )

    is_active = models.BooleanField(default=True)

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entidades_creadas'
    )

    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entidades_modificadas'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        ordering = ['-fecha_modificacion']

    def __str__(self):
        return self.nombre_empresa
        
# ─────────────────────────────────────────────
# EVIDENCIA
# ─────────────────────────────────────────────

class Evidencia(models.Model):

    TIPOS = [
        ('ASV', 'ASV Scan'),
        ('SAQ', 'SAQ'),
        ('POLITICA', 'Política'),
        ('CAPTURA', 'Captura'),
        ('FIREWALL', 'Firewall'),
        ('OTRO', 'Otro'),
    ]

    entidad = models.ForeignKey(
        'Entidad',
        on_delete=models.CASCADE,
        related_name='evidencias'
    )

    titulo = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default='OTRO'
    )

    archivo = models.FileField(
        upload_to='evidencias/%Y/%m/'
    )

    version = models.PositiveIntegerField(
        default=1
    )

    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evidencias_subidas'
    )

    fecha_subida = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    activa = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'

    def __str__(self):
        return self.titulo