from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import (
    TipoEntidad, Pais, TipoContrato, NivelRiesgo, TipoSAQ,
    TipoDocumento, EstadoCertificacion, TipoRol, Idioma,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _json_ok():
    return JsonResponse({"success": True})


def _toggle(model, pk):
    obj = get_object_or_404(model, pk=pk)
    obj.activo = not obj.activo
    obj.save()
    return _json_ok()


def _eliminar(model, pk):
    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    return _json_ok()


def _guardar_simple(request, model, campos_extra=None):
    """Helper para modelos con solo nombre y descripcion."""
    pk          = request.POST.get("pk")
    nombre      = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()

    if not nombre:
        return JsonResponse({"error": "El nombre es obligatorio."}, status=400)

    qs = model.objects.exclude(pk=pk) if pk else model.objects
    if qs.filter(nombre__iexact=nombre).exists():
        return JsonResponse({"error": "Ya existe un registro con ese nombre."}, status=400)

    defaults = {"descripcion": descripcion}
    if campos_extra:
        defaults.update(campos_extra)

    if pk:
        obj = get_object_or_404(model, pk=pk)
        obj.nombre = nombre
        for k, v in defaults.items():
            setattr(obj, k, v)
        obj.save()
    else:
        model.objects.create(nombre=nombre, **defaults)

    return _json_ok()


# ─────────────────────────────────────────────
# TIPOS DE ENTIDAD
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_entidad(request):
    if request.method == "POST":
        return _guardar_simple(request, TipoEntidad)
    return render(request, "catalogos/tipo_entidad.html",
                  {"items": TipoEntidad.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_entidad_toggle(request, pk):
    return _toggle(TipoEntidad, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_entidad_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(TipoEntidad, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# PAÍSES
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def paises(request):
    if request.method == "POST":
        pk     = request.POST.get("pk")
        nombre = request.POST.get("nombre", "").strip()
        codigo = request.POST.get("codigo", "").strip().upper()

        if not nombre or not codigo:
            return JsonResponse({"error": "Nombre y código son obligatorios."}, status=400)

        qs = Pais.objects.exclude(pk=pk) if pk else Pais.objects
        if qs.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"error": "Ya existe un país con ese nombre."}, status=400)

        if pk:
            obj = get_object_or_404(Pais, pk=pk)
            obj.nombre = nombre
            obj.codigo = codigo
            obj.save()
        else:
            Pais.objects.create(nombre=nombre, codigo=codigo)

        return _json_ok()

    return render(request, "catalogos/paises.html",
                  {"items": Pais.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def paises_toggle(request, pk):
    return _toggle(Pais, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def paises_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(Pais, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# TIPOS DE CONTRATO
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_contrato(request):
    if request.method == "POST":
        return _guardar_simple(request, TipoContrato)
    return render(request, "catalogos/tipo_contrato.html",
                  {"items": TipoContrato.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_contrato_toggle(request, pk):
    return _toggle(TipoContrato, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_contrato_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(TipoContrato, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# NIVELES DE RIESGO
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def nivel_riesgo(request):
    if request.method == "POST":
        pk          = request.POST.get("pk")
        nombre      = request.POST.get("nombre", "").strip()
        nivel       = request.POST.get("nivel", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()

        if not nombre or not nivel:
            return JsonResponse({"error": "Nombre y nivel son obligatorios."}, status=400)

        qs = NivelRiesgo.objects.exclude(pk=pk) if pk else NivelRiesgo.objects
        if qs.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"error": "Ya existe un registro con ese nombre."}, status=400)

        if pk:
            obj = get_object_or_404(NivelRiesgo, pk=pk)
            obj.nombre      = nombre
            obj.nivel       = nivel
            obj.descripcion = descripcion
            obj.save()
        else:
            NivelRiesgo.objects.create(nombre=nombre, nivel=nivel, descripcion=descripcion)

        return _json_ok()

    return render(request, "catalogos/nivel_riesgo.html",
                  {"items": NivelRiesgo.objects.all().order_by("nivel")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def nivel_riesgo_toggle(request, pk):
    return _toggle(NivelRiesgo, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def nivel_riesgo_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(NivelRiesgo, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# TIPOS DE SAQ
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_saq(request):
    if request.method == "POST":
        pk          = request.POST.get("pk")
        codigo      = request.POST.get("codigo", "").strip().upper()
        nombre      = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()

        if not codigo or not nombre:
            return JsonResponse({"error": "Código y nombre son obligatorios."}, status=400)

        qs = TipoSAQ.objects.exclude(pk=pk) if pk else TipoSAQ.objects
        if qs.filter(codigo__iexact=codigo).exists():
            return JsonResponse({"error": "Ya existe un SAQ con ese código."}, status=400)

        if pk:
            obj = get_object_or_404(TipoSAQ, pk=pk)
            obj.codigo      = codigo
            obj.nombre      = nombre
            obj.descripcion = descripcion
            obj.save()
        else:
            TipoSAQ.objects.create(codigo=codigo, nombre=nombre, descripcion=descripcion)

        return _json_ok()

    return render(request, "catalogos/tipo_saq.html",
                  {"items": TipoSAQ.objects.all().order_by("codigo")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_saq_toggle(request, pk):
    return _toggle(TipoSAQ, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_saq_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(TipoSAQ, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# TIPOS DE DOCUMENTO
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_documento(request):
    if request.method == "POST":
        return _guardar_simple(request, TipoDocumento)
    return render(request, "catalogos/tipo_documento.html",
                  {"items": TipoDocumento.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_documento_toggle(request, pk):
    return _toggle(TipoDocumento, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_documento_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(TipoDocumento, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# ESTADOS DE CERTIFICACIÓN
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def estado_certificacion(request):
    if request.method == "POST":
        return _guardar_simple(request, EstadoCertificacion)
    return render(request, "catalogos/estado_certificacion.html",
                  {"items": EstadoCertificacion.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def estado_certificacion_toggle(request, pk):
    return _toggle(EstadoCertificacion, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def estado_certificacion_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(EstadoCertificacion, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# TIPOS DE ROL
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_rol(request):
    if request.method == "POST":
        return _guardar_simple(request, TipoRol)
    return render(request, "catalogos/tipo_rol.html",
                  {"items": TipoRol.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_rol_toggle(request, pk):
    return _toggle(TipoRol, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def tipo_rol_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(TipoRol, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ─────────────────────────────────────────────
# IDIOMAS
# ─────────────────────────────────────────────

@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def idiomas(request):
    if request.method == "POST":
        pk     = request.POST.get("pk")
        nombre = request.POST.get("nombre", "").strip()
        codigo = request.POST.get("codigo", "").strip().lower()

        if not nombre or not codigo:
            return JsonResponse({"error": "Nombre y código son obligatorios."}, status=400)

        qs = Idioma.objects.exclude(pk=pk) if pk else Idioma.objects
        if qs.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"error": "Ya existe un idioma con ese nombre."}, status=400)

        if pk:
            obj = get_object_or_404(Idioma, pk=pk)
            obj.nombre = nombre
            obj.codigo = codigo
            obj.save()
        else:
            Idioma.objects.create(nombre=nombre, codigo=codigo)

        return _json_ok()

    return render(request, "catalogos/idiomas.html",
                  {"items": Idioma.objects.all().order_by("nombre")})


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def idiomas_toggle(request, pk):
    return _toggle(Idioma, pk)


@login_required
@permission_required('catalogos.gestionar_catalogos', raise_exception=True)
def idiomas_eliminar(request, pk):
    if request.method == "POST":
        return _eliminar(Idioma, pk)
    return JsonResponse({"error": "Método no permitido"}, status=405)