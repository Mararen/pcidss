from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from .models import Ticket, ComentarioTicket, Categoria, EstadoTicket
from users.models import Entidad


# ── Helper de permisos ────────────────────────────────────────────────────────

def es_helpdesk(user):
    """Superusuario o miembro del grupo 'Helpdesk'."""
    return user.is_superuser or user.groups.filter(name='Helpdesk').exists()


# ── Lista de tickets ──────────────────────────────────────────────────────────

@login_required
def ticket_lista(request):
    qs = Ticket.objects.select_related(
        'usuario', 'asignado_a', 'entidad', 'categoria'
    ).order_by('-fecha_creacion')

    # Helpdesk ve todos; usuario normal solo los suyos
    if not es_helpdesk(request.user):
        qs = qs.filter(usuario=request.user)

    # Filtros opcionales
    estado    = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')
    if estado:
        qs = qs.filter(estado=estado)
    if prioridad:
        qs = qs.filter(prioridad=prioridad)

    return render(request, 'helpdesk/ticket_lista.html', {
        'tickets':     qs,
        'es_helpdesk': es_helpdesk(request.user),
    })


# ── Crear ticket (cualquier usuario autenticado) ──────────────────────────────

@login_required
def ticket_nuevo(request):
    if request.method == 'POST':
        Ticket.objects.create(
            titulo       = request.POST.get('titulo'),
            descripcion  = request.POST.get('descripcion'),
            usuario      = request.user,
            entidad_id   = request.POST.get('entidad'),
            categoria_id = request.POST.get('categoria') or None,
            prioridad    = request.POST.get('prioridad', 'media'),
        )
        return redirect('helpdesk:ticket_lista')

    return render(request, 'helpdesk/ticket_nuevo.html', {
        'entidades':  Entidad.objects.all(),
        'categorias': Categoria.objects.all(),
    })


# ── Detalle de ticket ─────────────────────────────────────────────────────────

@login_required
def ticket_detalle(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related('usuario', 'asignado_a', 'entidad', 'categoria'),
        pk=pk
    )

    # Un usuario normal solo puede ver sus propios tickets
    if not es_helpdesk(request.user) and ticket.usuario != request.user:
        raise PermissionDenied

    comentarios = ticket.comentarios.select_related('usuario').order_by('fecha')

    return render(request, 'helpdesk/ticket_detalle.html', {
        'ticket':      ticket,
        'comentarios': comentarios,
        'estados':     EstadoTicket.choices,
        'es_helpdesk': es_helpdesk(request.user),
    })


# ── Agregar comentario ────────────────────────────────────────────────────────

@login_required
@require_POST
def agregar_comentario(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Solo el dueño del ticket o helpdesk pueden comentar
    if not es_helpdesk(request.user) and ticket.usuario != request.user:
        raise PermissionDenied

    texto = request.POST.get('comentario', '').strip()
    if texto:
        ComentarioTicket.objects.create(
            ticket     = ticket,
            usuario    = request.user,
            comentario = texto,
        )

    return redirect('helpdesk:ticket_detalle', pk=pk)


# ── Cambiar estado (solo Helpdesk) ────────────────────────────────────────────

@login_required
@require_POST
def cambiar_estado(request, pk):
    if not es_helpdesk(request.user):
        raise PermissionDenied

    ticket = get_object_or_404(Ticket, pk=pk)

    nuevo_estado = request.POST.get('estado')
    comentario   = request.POST.get('comentario', '').strip()

    if nuevo_estado in dict(EstadoTicket.choices):
        ticket.estado = nuevo_estado
        ticket.save(update_fields=['estado', 'fecha_actualizacion'])

        # Registrar el cambio como comentario visible para todos
        nota = f'Estado cambiado a "{ticket.get_estado_display()}".'
        if comentario:
            nota += f'\n\n{comentario}'

        ComentarioTicket.objects.create(
            ticket     = ticket,
            usuario    = request.user,
            comentario = nota,
            interno    = False,   # visible para el usuario final
        )

    return redirect('helpdesk:ticket_detalle', pk=pk)