from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Ticket, ComentarioTicket, Categoria, EstadoTicket
from users.models import Entidad


@login_required
def ticket_lista(request):
    qs = Ticket.objects.select_related(
        'usuario', 'asignado_a', 'entidad', 'categoria'
    ).order_by('-fecha_creacion')

    if not request.user.is_superuser:
        qs = qs.filter(usuario=request.user)

    return render(request, 'helpdesk/ticket_lista.html', {
        'tickets': qs
    })


@login_required
def ticket_nuevo(request):
    if request.method == 'POST':
        Ticket.objects.create(
            titulo=request.POST.get('titulo'),
            descripcion=request.POST.get('descripcion'),
            usuario=request.user,
            entidad_id=request.POST.get('entidad'),
            categoria_id=request.POST.get('categoria'),
            prioridad=request.POST.get('prioridad'),
        )
        return redirect('helpdesk:ticket_lista')

    return render(request, 'helpdesk/ticket_nuevo.html', {
        'entidades': Entidad.objects.all(),
        'categorias': Categoria.objects.all(),
    })


@login_required
def ticket_detalle(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related('usuario', 'asignado_a', 'entidad', 'categoria'),
        pk=pk
    )

    comentarios = ticket.comentarios.select_related('usuario').order_by('fecha')

    return render(request, 'helpdesk/ticket_detalle.html', {
        'ticket': ticket,
        'comentarios': comentarios
    })


@login_required
@require_POST
def agregar_comentario(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    ComentarioTicket.objects.create(
        ticket=ticket,
        usuario=request.user,
        comentario=request.POST.get('comentario')
    )

    return redirect('helpdesk:ticket_detalle', pk=pk)


@login_required
@require_POST
def cambiar_estado(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    nuevo_estado = request.POST.get('estado')

    if nuevo_estado in dict(EstadoTicket.choices):
        ticket.estado = nuevo_estado
        ticket.save()

    return JsonResponse({'success': True})