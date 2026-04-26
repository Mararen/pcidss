from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Prioridad(models.TextChoices):
    BAJA   = 'baja',   'Baja'
    MEDIA  = 'media',  'Media'
    ALTA   = 'alta',   'Alta'
    CRITICA= 'critica','Crítica'


class EstadoTicket(models.TextChoices):
    ABIERTO     = 'abierto', 'Abierto'
    EN_PROCESO  = 'proceso', 'En proceso'
    RESUELTO    = 'resuelto','Resuelto'
    CERRADO     = 'cerrado', 'Cerrado'


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Ticket(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')

    entidad = models.ForeignKey('users.Entidad', on_delete=models.CASCADE)

    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)

    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    estado    = models.CharField(max_length=20, choices=EstadoTicket.choices, default=EstadoTicket.ABIERTO)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'#{self.id} - {self.titulo}'


class ComentarioTicket(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    interno = models.BooleanField(default=False)  # para notas internas

    def __str__(self):
        return f'Comentario #{self.id} - Ticket {self.ticket_id}'


class ArchivoTicket(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='tickets/')
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
