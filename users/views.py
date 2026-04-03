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

from .models import Entidad, TipoSAQ, SeccionSAQ, PreguntaSAQ, PreguntaEnSeccion


# ─── Login / Logout ───────────────────────────────────────

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "users/login.html", {"error": "Credenciales incorrectas"})
    return render(request, "users/login.html")


@login_required
def dashboard(request):
    return render(request, "users/dashboard.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ─── Forgot Password ──────────────────────────────────────

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
                    'subject': 'Restablecer contraseña — PCI Cert Pro',
                    'textContent': f'Haz clic aquí para restablecer tu contraseña:\n\n{reset_link}',
                }
            )
        except User.DoesNotExist:
            pass
        message = 'Si ese correo está registrado, recibirás un enlace en breve.'
    return render(request, 'users/forgot_password.html', {'message': message})


# ─── Mixin ────────────────────────────────────────────────

class SoloAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


# ═══════════════════════════════════════════════════════════
# USUARIOS
# ═══════════════════════════════════════════════════════════

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
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all().order_by("-date_joined")
        search = self.request.GET.get("buscar")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset


class UsuarioDetalleView(SoloAdminMixin, DetailView):
    model = User
    template_name = "users/usuario_detalle.html"
    context_object_name = "usuario"


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
    usuario = get_object_or_404(User, pk=pk)
    if request.user.is_superuser:
        usuario.is_active = not usuario.is_active
        usuario.save()
    return redirect("usuarios_lista")


# ═══════════════════════════════════════════════════════════
# ENTIDADES
# ═══════════════════════════════════════════════════════════

class EntidadForm(forms.ModelForm):
    class Meta:
        model = Entidad
        fields = ["usuario", "nombre_empresa", "dba", "email", "sitio_web", "contacto"]


class EntidadListView(SoloAdminMixin, ListView):
    model = Entidad
    template_name = "users/entidades_lista.html"
    context_object_name = "entidades"
    paginate_by = 5

    def get_queryset(self):
        queryset = Entidad.objects.select_related("usuario").order_by("-fecha_modificacion")
        search = self.request.GET.get("buscar")
        if search:
            queryset = queryset.filter(
                Q(nombre_empresa__icontains=search) |
                Q(dba__icontains=search) |
                Q(email__icontains=search) |
                Q(contacto__icontains=search)
            )
        return queryset


class EntidadDetalleView(SoloAdminMixin, DetailView):
    model = Entidad
    template_name = "users/entidad_detalle.html"
    context_object_name = "entidad"


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
    entidad = get_object_or_404(Entidad, pk=pk)
    if request.user.is_superuser:
        entidad.is_active = not entidad.is_active
        entidad.save()
    return redirect("entidades_lista")


# ═══════════════════════════════════════════════════════════
# SAQ
# ═══════════════════════════════════════════════════════════

class TipoSAQForm(forms.ModelForm):
    class Meta:
        model = TipoSAQ
        fields = ["nombre", "codigo", "descripcion"]


class SeccionSAQForm(forms.ModelForm):
    class Meta:
        model = SeccionSAQ
        fields = ["nombre", "orden"]


class PreguntaSAQForm(forms.ModelForm):
    class Meta:
        model = PreguntaSAQ
        fields = ["texto", "referencia_pci", "activa"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3}),
        }


@login_required
def saq_lista(request):
    tipos = TipoSAQ.objects.prefetch_related("secciones").all()
    return render(request, "users/saq_lista.html", {"tipos": tipos})


@login_required
def saq_detalle(request, tipo_pk, seccion_pk=None):
    tipo      = get_object_or_404(TipoSAQ, pk=tipo_pk)
    secciones = tipo.secciones.prefetch_related("preguntas").all()

    if seccion_pk:
        seccion_activa = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    else:
        seccion_activa = secciones.first()

    preguntas = []
    if seccion_activa:
        preguntas = PreguntaEnSeccion.objects.filter(
            seccion=seccion_activa
        ).select_related("pregunta").order_by("orden")

    return render(request, "users/saq_detalle.html", {
        "tipo":           tipo,
        "secciones":      secciones,
        "seccion_activa": seccion_activa,
        "preguntas":      preguntas,
    })


@login_required
def saq_tipo_crear(request):
    form = TipoSAQForm(request.POST or None)
    if form.is_valid():
        tipo = form.save()
        messages.success(request, f"SAQ '{tipo.nombre}' creado correctamente.")
        return redirect("saq_detalle", tipo_pk=tipo.pk)
    return render(request, "users/saq_tipo_form.html", {"form": form})


@login_required
def saq_tipo_editar(request, tipo_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)
    form = TipoSAQForm(request.POST or None, instance=tipo)
    if form.is_valid():
        form.save()
        messages.success(request, "SAQ actualizado correctamente.")
        return redirect("saq_detalle", tipo_pk=tipo.pk)
    return render(request, "users/saq_tipo_form.html", {"form": form, "tipo": tipo})


@login_required
def saq_seccion_crear(request, tipo_pk):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)
    form = SeccionSAQForm(request.POST or None)
    if form.is_valid():
        seccion = form.save(commit=False)
        seccion.tipo_saq = tipo
        seccion.save()
        messages.success(request, f"Sección '{seccion.nombre}' creada.")
        return redirect("saq_detalle_seccion", tipo_pk=tipo.pk, seccion_pk=seccion.pk)
    return render(request, "users/saq_seccion_form.html", {"form": form, "tipo": tipo})


@login_required
def saq_seccion_editar(request, tipo_pk, seccion_pk):
    tipo    = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    form    = SeccionSAQForm(request.POST or None, instance=seccion)
    if form.is_valid():
        form.save()
        messages.success(request, "Sección actualizada.")
        return redirect("saq_detalle_seccion", tipo_pk=tipo.pk, seccion_pk=seccion.pk)
    return render(request, "users/saq_seccion_form.html", {
        "form": form, "tipo": tipo, "seccion": seccion
    })


@login_required
def saq_seccion_eliminar(request, tipo_pk, seccion_pk):
    tipo    = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    if request.method == "POST":
        seccion.delete()
        messages.success(request, "Sección eliminada.")
        return redirect("saq_detalle", tipo_pk=tipo.pk)
    return render(request, "users/saq_seccion_eliminar.html", {
        "tipo": tipo, "seccion": seccion
    })


@login_required
def saq_pregunta_agregar(request, tipo_pk, seccion_pk):
    tipo    = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    form    = PreguntaSAQForm(request.POST or None)
    if form.is_valid():
        pregunta = form.save()
        ultimo_orden = PreguntaEnSeccion.objects.filter(seccion=seccion).count()
        PreguntaEnSeccion.objects.create(
            pregunta=pregunta, seccion=seccion, orden=ultimo_orden + 1
        )
        messages.success(request, "Pregunta agregada.")
        return redirect("saq_detalle_seccion", tipo_pk=tipo.pk, seccion_pk=seccion.pk)
    return render(request, "users/saq_pregunta_form.html", {
        "form": form, "tipo": tipo, "seccion": seccion
    })


@login_required
def saq_pregunta_editar(request, tipo_pk, seccion_pk, pregunta_pk):
    tipo     = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion  = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    pregunta = get_object_or_404(PreguntaSAQ, pk=pregunta_pk)
    form     = PreguntaSAQForm(request.POST or None, instance=pregunta)
    if form.is_valid():
        form.save()
        messages.success(request, "Pregunta actualizada.")
        return redirect("saq_detalle_seccion", tipo_pk=tipo.pk, seccion_pk=seccion.pk)
    return render(request, "users/saq_pregunta_form.html", {
        "form": form, "tipo": tipo, "seccion": seccion, "pregunta": pregunta
    })


@login_required
def saq_pregunta_eliminar(request, tipo_pk, seccion_pk, pregunta_pk):
    tipo    = get_object_or_404(TipoSAQ, pk=tipo_pk)
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk, tipo_saq=tipo)
    entrada = get_object_or_404(PreguntaEnSeccion, pregunta_id=pregunta_pk, seccion=seccion)
    if request.method == "POST":
        entrada.delete()
        messages.success(request, "Pregunta eliminada de la sección.")
        return redirect("saq_detalle_seccion", tipo_pk=tipo.pk, seccion_pk=seccion.pk)
    return render(request, "users/saq_pregunta_eliminar.html", {
        "tipo": tipo, "seccion": seccion, "entrada": entrada
    })
