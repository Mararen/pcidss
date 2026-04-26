from django.contrib import admin
from .models import Ticket, ComentarioTicket, Categoria


class ComentarioInline(admin.TabularInline):
    model = ComentarioTicket
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'usuario', 'estado', 'prioridad', 'asignado_a', 'fecha_creacion')
    list_filter = ('estado', 'prioridad', 'categoria')
    search_fields = ('titulo', 'descripcion')
    inlines = [ComentarioInline]


admin.site.register(Categoria)