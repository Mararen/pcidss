import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

from .models import PreguntaSAQ, PreTest, RespuestaPreTest, TipoSAQ
from users.models import Entidad
from users.views import registrar_log

TIPOS_SAQ_ORDEN = ['A', 'AEP', 'B', 'BIP', 'C', 'CTV', 'D-COMERCIO', 'D-PROVEEDOR']
SAQ_TYPES = [(t, t) for t in TIPOS_SAQ_ORDEN]

TIPO_INPUT_CHOICES = [
    ('elegibilidad',   'Sí / No / N/A / No probado'),
    ('checkbox_si_no', 'Sí / No'),
    ('checkbox_multi', 'Selección múltiple'),
    ('select',         'Lista desplegable'),
    ('texto_corto',    'Texto corto'),
    ('texto_largo',    'Texto largo'),
    ('numero',         'Número'),
    ('fecha',          'Fecha'),
]


# ════════════════════════════════════════════════════════════════
# BANCO DE PREGUNTAS SAQ
# ════════════════════════════════════════════════════════════════

@login_required
def saq_lista(request):
    """Lista paginada de preguntas con filtro por SAQ y búsqueda."""
    qs = PreguntaSAQ.objects.filter(activo=True).order_by('numero')

    tipo   = request.GET.get('tipo', '')
    buscar = request.GET.get('buscar', '')

    if tipo:
        qs = qs.filter(tipo_saq=tipo)
    if buscar:
        qs = qs.filter(
            Q(pregunta_es__icontains=buscar) | Q(pregunta_en__icontains=buscar)
        )

    conteos = {'ALL': PreguntaSAQ.objects.filter(activo=True).count()}
    for t in TIPOS_SAQ_ORDEN:
        conteos[t] = PreguntaSAQ.objects.filter(activo=True, tipo_saq=t).count()

    paginator = Paginator(qs, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'saq/saq_lista.html', {
        'page_obj':    page_obj,
        'conteos':     conteos,
        'tipos':       SAQ_TYPES,
        'tipo_filtro': tipo,
        'buscar':      buscar,
    })


@login_required
@permission_required('saq.add_preguntasaq', raise_exception=True)
def saq_crear(request):
    """GET → formulario vacío. POST → crea pregunta y redirige a lista."""
    errors = []

    if request.method == 'POST':
        numero          = request.POST.get('numero', '').strip()
        tipo_saq        = request.POST.get('tipo_saq', '').strip()
        tipos_saq_extra = request.POST.get('tipos_saq_extra', '').strip()
        tipo_input      = request.POST.get('tipo_input', 'elegibilidad')
        seccion_aoc     = request.POST.get('seccion_aoc', 'Part 2h. Eligibility').strip()
        pregunta_es     = request.POST.get('pregunta_es', '').strip()
        pregunta_en     = request.POST.get('pregunta_en', '').strip()
        opciones_json   = request.POST.get('opciones_json', '').strip()
        max_chars       = request.POST.get('max_chars', '').strip() or None

        # Validaciones
        if not numero or not tipo_saq or not pregunta_es:
            errors.append('Número, Tipo SAQ y Pregunta ES son obligatorios.')
        elif not numero.isdigit():
            errors.append('El número debe ser un entero positivo.')
        elif PreguntaSAQ.objects.filter(numero=numero).exists():
            errors.append(f'Ya existe una pregunta con el número {numero}.')

        opciones_parsed = None
        if opciones_json:
            try:
                opciones_parsed = json.loads(opciones_json)
            except json.JSONDecodeError:
                errors.append('Opciones JSON no tiene formato válido (debe ser una lista, ej: ["Op1","Op2"]).')

        if not errors:
            p = PreguntaSAQ.objects.create(
                numero          = int(numero),
                tipo_saq        = tipo_saq,
                tipos_saq_extra = tipos_saq_extra,
                tipo_input      = tipo_input,
                seccion_aoc     = seccion_aoc,
                pregunta_es     = pregunta_es,
                pregunta_en     = pregunta_en,
                opciones_json   = opciones_parsed,
                max_chars       = int(max_chars) if max_chars and max_chars.isdigit() else None,
            )
            registrar_log(request, 'CREATE', 'SAQ', f'Pregunta #{p.numero} creada')
            return redirect('saq:saq_lista')

        # Rellenar el form con lo enviado para no perder los datos
        form_data = request.POST

    else:
        form_data = {}

    return render(request, 'saq/saq_form.html', {
        'titulo':              'Nueva pregunta SAQ',
        'accion':              'Crear',
        'tipos':               SAQ_TYPES,
        'tipo_input_choices':  TIPO_INPUT_CHOICES,
        'form':                form_data,
        'errors':              errors,
    })


@login_required
@permission_required('saq.change_preguntasaq', raise_exception=True)
def saq_editar(request, pk):
    """GET → formulario con datos actuales. POST → actualiza y redirige a lista."""
    pregunta = get_object_or_404(PreguntaSAQ, pk=pk)
    errors   = []

    if request.method == 'POST':
        tipo_saq        = request.POST.get('tipo_saq', '').strip()
        tipos_saq_extra = request.POST.get('tipos_saq_extra', '').strip()
        tipo_input      = request.POST.get('tipo_input', pregunta.tipo_input)
        seccion_aoc     = request.POST.get('seccion_aoc', '').strip()
        pregunta_es     = request.POST.get('pregunta_es', '').strip()
        pregunta_en     = request.POST.get('pregunta_en', '').strip()
        opciones_json   = request.POST.get('opciones_json', '').strip()
        max_chars       = request.POST.get('max_chars', '').strip() or None

        if not tipo_saq or not pregunta_es:
            errors.append('Tipo SAQ y Pregunta ES son obligatorios.')

        opciones_parsed = pregunta.opciones_json  # mantiene valor actual si no se envía
        if opciones_json:
            try:
                opciones_parsed = json.loads(opciones_json)
            except json.JSONDecodeError:
                errors.append('Opciones JSON no tiene formato válido.')

        if not errors:
            pregunta.tipo_saq        = tipo_saq
            pregunta.tipos_saq_extra = tipos_saq_extra
            pregunta.tipo_input      = tipo_input
            pregunta.seccion_aoc     = seccion_aoc
            pregunta.pregunta_es     = pregunta_es
            pregunta.pregunta_en     = pregunta_en
            pregunta.opciones_json   = opciones_parsed
            pregunta.max_chars       = int(max_chars) if max_chars and max_chars.isdigit() else None
            pregunta.save()
            registrar_log(request, 'UPDATE', 'SAQ', f'Pregunta #{pregunta.numero} actualizada')
            return redirect('saq:saq_lista')

        form_data = request.POST

    else:
        # Pre-cargar datos actuales en el "form dict"
        form_data = {
            'numero':          pregunta.numero,
            'tipo_saq':        pregunta.tipo_saq,
            'tipos_saq_extra': pregunta.tipos_saq_extra,
            'tipo_input':      pregunta.tipo_input,
            'seccion_aoc':     pregunta.seccion_aoc,
            'pregunta_es':     pregunta.pregunta_es,
            'pregunta_en':     pregunta.pregunta_en,
            'opciones_json':   json.dumps(pregunta.opciones_json) if pregunta.opciones_json else '',
            'max_chars':       pregunta.max_chars or '',
        }

    return render(request, 'saq/saq_form.html', {
        'titulo':             f'Editar pregunta #{pregunta.numero}',
        'accion':             'Guardar cambios',
        'tipos':              SAQ_TYPES,
        'tipo_input_choices': TIPO_INPUT_CHOICES,
        'form':               form_data,
        'pregunta':           pregunta,
        'errors':             errors,
    })


@login_required
@permission_required('saq.delete_preguntasaq', raise_exception=True)
def saq_eliminar(request, pk):
    """GET → confirmación. POST → elimina y redirige a lista."""
    pregunta = get_object_or_404(PreguntaSAQ, pk=pk)

    if request.method == 'POST':
        numero = pregunta.numero
        pregunta.delete()
        registrar_log(request, 'DELETE', 'SAQ', f'Pregunta #{numero} eliminada')
        return redirect('saq:saq_lista')

    return render(request, 'saq/saq_confirmar_eliminar.html', {'obj': pregunta})


# ════════════════════════════════════════════════════════════════
# PRETEST — LISTA
# ════════════════════════════════════════════════════════════════

@login_required
def pretest_lista(request):
    qs = PreTest.objects.select_related('entidad', 'creado_por').order_by('-fecha_creacion')

    entidad_id = request.GET.get('entidad')
    if entidad_id:
        qs = qs.filter(entidad_id=entidad_id)

    paginator = Paginator(qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'saq/pretest_lista.html', {
        'page_obj':   page_obj,
        'entidades':  Entidad.objects.filter(is_active=True).order_by('nombre_empresa'),
        'entidad_id': entidad_id,
    })


# ════════════════════════════════════════════════════════════════
# PRETEST — NUEVO
# ════════════════════════════════════════════════════════════════

@login_required
def pretest_nuevo(request):
    if request.method == 'POST':
        entidad = get_object_or_404(Entidad, pk=request.POST.get('entidad'))
        pretest = PreTest.objects.create(entidad=entidad, creado_por=request.user)
        registrar_log(request, 'CREATE', 'PRETEST',
                      f'PreTest #{pretest.pk} para {entidad}')
        return redirect('saq:pretest_cuestionario', pretest.pk)

    return render(request, 'saq/pretest_nuevo.html', {
        'entidades': Entidad.objects.filter(is_active=True).order_by('nombre_empresa'),
    })


# ════════════════════════════════════════════════════════════════
# PRETEST — CUESTIONARIO
# ════════════════════════════════════════════════════════════════

@login_required
def pretest_cuestionario(request, pk):
    pretest   = get_object_or_404(PreTest, pk=pk)
    preguntas = PreguntaSAQ.objects.filter(activo=True).order_by('numero')

    resp_raw  = pretest.respuestas.select_related('pregunta').all()
    resp_dict = {str(r.pregunta_id): r.respuesta_texto for r in resp_raw}

    paginator  = Paginator(preguntas, 10)
    num_pagina = int(request.GET.get('pagina', 1))
    page_obj   = paginator.get_page(num_pagina)

    total       = preguntas.count()
    respondidas = len(resp_dict)

    return render(request, 'saq/pretest_cuestionario.html', {
        'pretest':                   pretest,
        'page_obj':                  page_obj,
        'paginator':                 paginator,
        'num_pagina':                num_pagina,
        'total':                     total,
        'respondidas':               respondidas,
        'porcentaje':                round(respondidas / total * 100) if total else 0,
        'respuestas_guardadas_json': json.dumps(resp_dict),
    })


# ════════════════════════════════════════════════════════════════
# PRETEST — GUARDAR RESPUESTA (AJAX)
# ════════════════════════════════════════════════════════════════

@login_required
@require_POST
def pretest_guardar_respuesta(request, pk):
    pretest = get_object_or_404(PreTest, pk=pk)
    data    = json.loads(request.body)

    pregunta = get_object_or_404(PreguntaSAQ, pk=data['pregunta_id'])
    valor    = data.get('respuesta', '')

    if isinstance(valor, list):
        valor = json.dumps(valor)

    RespuestaPreTest.objects.update_or_create(
        pretest=pretest,
        pregunta=pregunta,
        defaults={'respuesta_texto': valor}
    )

    total       = PreguntaSAQ.objects.filter(activo=True).count()
    respondidas = pretest.respuestas.count()

    return JsonResponse({
        'success':    True,
        'total':      total,
        'respondidas': respondidas,
        'porcentaje': round(respondidas / total * 100) if total else 0,
    })

# ════════════════════════════════════════════════════════════════
# PRETEST — ELIMINAR
# ════════════════════════════════════════════════════════════════

@login_required
def pretest_eliminar(request, pk):
    pretest = get_object_or_404(PreTest, pk=pk)

    if request.method == 'POST':
        entidad = str(pretest.entidad)
        pretest.delete()
        registrar_log(request, 'DELETE', 'PRETEST',
                      f'PreTest #{pk} de {entidad} eliminado')
        return redirect('saq:pretest_lista')

    return render(request, 'saq/pretest_confirmar_eliminar.html', {'pretest': pretest})

# ════════════════════════════════════════════════════════════════
# PRETEST — RESULTADOS
# ════════════════════════════════════════════════════════════════

@login_required
def pretest_resultados(request, pk):
    pretest  = get_object_or_404(PreTest, pk=pk)
    conteos  = pretest.calcular_resultado()

    total_preguntas   = PreguntaSAQ.objects.filter(activo=True).count()
    total_respondidas = pretest.respuestas.count()

    resultado_por_tipo = []
    for tipo in TIPOS_SAQ_ORDEN:
        c = conteos[tipo]
        resultado_por_tipo.append({
            'tipo':           tipo,
            'label':          dict(TipoSAQ.choices).get(tipo, tipo),
            'total':          c['total'],
            'si':             c['si'],
            'no':             c['no'],
            'na':             c['na'],
            'no_probado':     c['no_probado'],
            'pct':            c['pct'],
            'elegible':       c['elegible'],
            'es_recomendado': c['es_recomendado'],
        })

    respuestas_resumen = []
    for resp in pretest.respuestas.select_related('pregunta').order_by('pregunta__numero'):
        respuestas_resumen.append({
            'numero':     resp.pregunta.numero,
            'tipo_saq':   resp.pregunta.tipo_saq,
            'seccion':    resp.pregunta.seccion_aoc,
            'pregunta':   resp.pregunta.pregunta_es,
            'respuesta':  resp.get_valor_display(),
            'tipo_input': resp.pregunta.tipo_input,
        })

    return render(request, 'saq/pretest_resultados.html', {
        'pretest':            pretest,
        'resultado_por_tipo': resultado_por_tipo,
        'saq_recomendado':    pretest.saq_recomendado,
        'saq_info':           PreTest.get_saq_info_todos().get(pretest.saq_recomendado, ''),
        'saq_info_todos':     PreTest.get_saq_info_todos(),
        'total_preguntas':    total_preguntas,
        'total_respondidas':  total_respondidas,
        'respuestas_resumen': respuestas_resumen,
    })