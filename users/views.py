import os
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django import forms
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Entidad, TipoSAQ, SeccionSAQ, PreguntaSAQ, PreguntaEnSeccion


# ─── LOGIN ──────────────────────────────────────────────

def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        if user:
            login(request, user)
            return redirect("dashboard")
        return render(request, "users/login.html", {"error": "Credenciales incorrectas"})
    return render(request, "users/login.html")


@login_required
def dashboard(request):
    return render(request, "users/dashboard.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ─── PASSWORD RESET ─────────────────────────────────────

def forgot_password(request):
    message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

            requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': os.environ.get('BREVO_API_KEY'),
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': {'name': 'PCI Cert Pro', 'email': 'pcicertpro@outlook.com'},
                    'to': [{'email': email}],
                    'subject': 'Restablecer contraseña',
                    'textContent': reset_link,
                }
            )
        except User.DoesNotExist:
            pass

        message = 'Si el correo existe, recibirás instrucciones.'

    return render(request, 'users/forgot_password.html', {'message': message})


# ─── MIXIN ──────────────────────────────────────────────

class SoloAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


# ════════════════════════════════════════════════════════
# USUARIOS
# ════════════════════════════════════════════════════════

class UsuarioCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]


class UsuarioListView(SoloAdminMixin, ListView):
    model = User
    template_name = "users/usuarios_lista.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        q = self.request.GET.get("buscar")
        qs = User.objects.all().order_by("-date_joined")
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q)
            )
        return qs


class UsuarioDetalleView(SoloAdminMixin, DetailView):
    model = User
    template_name = "users/usuario_detalle.html"


class UsuarioCreateView(SoloAdminMixin, CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")


class UsuarioUpdateView(SoloAdminMixin, UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")


@login_required
def usuario_toggle(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.user.is_superuser:
        u.is_active = not u.is_active
        u.save()
    return redirect("usuarios_lista")


# ════════════════════════════════════════════════════════
# ENTIDADES
# ════════════════════════════════════════════════════════

class EntidadForm(forms.ModelForm):
    class Meta:
        model = Entidad
        fields = "__all__"


class EntidadListView(SoloAdminMixin, ListView):
    model = Entidad
    template_name = "users/entidades_lista.html"


class EntidadCreateView(SoloAdminMixin, CreateView):
    model = Entidad
    form_class = EntidadForm
    template_name = "users/entidades_form.html"
    success_url = reverse_lazy("entidades_lista")


class EntidadUpdateView(SoloAdminMixin, UpdateView):
    model = Entidad
    form_class = EntidadForm
    template_name = "users/entidades_form.html"
    success_url = reverse_lazy("entidades_lista")


@login_required
def entidad_toggle(request, pk):
    e = get_object_or_404(Entidad, pk=pk)
    e.is_active = not e.is_active
    e.save()
    return redirect("entidades_lista")


# ════════════════════════════════════════════════════════
# SAQ
# ════════════════════════════════════════════════════════

@login_required
def saq_lista(request):
    return render(request, "users/saq_lista.html", {
        "tipos": TipoSAQ.objects.all()
    })


@login_required
def saq_detalle(request, tipo_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)

    secciones = tipo.secciones.all().order_by("orden")
    seccion_activa = secciones.first()

    preguntas = []
    if seccion_activa:
        preguntas = PreguntaEnSeccion.objects.filter(
            seccion=seccion_activa
        ).select_related("pregunta").order_by("orden")

    return render(request, "users/saq.html", {
        "tipo": tipo,
        "secciones": secciones,
        "seccion_activa": seccion_activa,
        "preguntas": preguntas
    })


@login_required
def saq_detalle_seccion(request, tipo_pk, seccion_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)

    preguntas = PreguntaEnSeccion.objects.filter(
        seccion=seccion
    ).select_related("pregunta").order_by("orden")

    return render(request, "users/saq.html", {
        "tipo": tipo,
        "secciones": tipo.secciones.all(),
        "seccion_activa": seccion,
        "preguntas": preguntas
    })


# ─── SECCIONES (AJAX) ───────────────────────────────────

@login_required
@require_POST
def saq_seccion_crear(request, tipo_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)

    nombre = request.POST.get("nombre")
    if not nombre:
        return JsonResponse({"success": False})

    orden = tipo.secciones.count() + 1

    seccion = SeccionSAQ.objects.create(
        tipo_saq=tipo,
        nombre=nombre,
        orden=orden
    )

    return JsonResponse({
        "success": True,
        "id": seccion.id,
        "nombre": seccion.nombre
    })


# ─── PREGUNTAS (AJAX CORE) ──────────────────────────────

@login_required
@require_POST
def saq_pregunta_ajax_crear(request, tipo_pk, seccion_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)

    texto = request.POST.get("texto")
    referencia = request.POST.get("referencia_pci")
    activa = request.POST.get("activa") == "true"

    if not texto:
        return JsonResponse({"success": False, "error": "Texto requerido"})

    # REUTILIZACIÓN DE PREGUNTAS
    pregunta, created = PreguntaSAQ.objects.get_or_create(
        texto=texto,
        referencia_pci=referencia,
        defaults={"activa": activa}
    )

    orden = PreguntaEnSeccion.objects.filter(seccion=seccion).count() + 1

    entrada = PreguntaEnSeccion.objects.create(
        pregunta=pregunta,
        seccion=seccion,
        orden=orden
    )

    return JsonResponse({
        "success": True,
        "pregunta": {
            "id": pregunta.id,
            "texto": pregunta.texto,
            "referencia_pci": pregunta.referencia_pci,
            "activa": pregunta.activa,
            "orden": entrada.orden
        }
    })


@login_required
@require_POST
def saq_pregunta_eliminar(request, tipo_pk, seccion_pk, pregunta_pk):
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk)
    pregunta = get_object_or_404(PreguntaSAQ, pk=pregunta_pk)

    PreguntaEnSeccion.objects.filter(
        seccion=seccion,
        pregunta=pregunta
    ).delete()

    if not PreguntaEnSeccion.objects.filter(pregunta=pregunta).exists():
        pregunta.delete()

    return JsonResponse({"success": True})