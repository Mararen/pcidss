# Imports

import os
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import Entidad


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
            return render(request, "users/login.html", {
                "error": "Credenciales incorrectas"
            })

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
            reset_link = request.build_absolute_uri(
                f'/reset-password/{uid}/{token}/'
            )
            requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {os.environ.get("RESEND_API_KEY")}',
                    'Content-Type': 'application/json',
                },
                json={
                    'from': 'onboarding@resend.dev',
                    'to': [email],
                    'subject': 'Restablecer contraseña — PCI Cert Pro',
                    'text': f'Haz clic aquí para restablecer tu contraseña:\n\n{reset_link}',
                }
            )
        except User.DoesNotExist:
            pass  # No revelamos si el correo existe (seguridad)

        # Siempre mostramos el mismo mensaje
        message = 'Si ese correo está registrado, recibirás un enlace en breve.'

    return render(request, 'users/forgot_password.html', {'message': message})


# ─── Mixin ────────────────────────────────────────────────

class SoloAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


# ─── Forms Usuarios ───────────────────────────────────────

class UsuarioCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]


# ─── CRUD Usuarios ────────────────────────────────────────

class UsuarioListView(SoloAdminMixin, ListView):
    model = User
    template_name = "users/usuarios_lista.html"
    context_object_name = "usuarios"
    paginate_by = 5

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


class UsuarioDeleteView(SoloAdminMixin, DeleteView):
    model = User
    template_name = "users/usuarios_eliminar.html"
    success_url = reverse_lazy("usuarios_lista")


# ─── Forms Entidades ──────────────────────────────────────

class EntidadForm(forms.ModelForm):
    class Meta:
        model = Entidad
        fields = [
            "usuario",
            "nombre_empresa",
            "dba",
            "email",
            "sitio_web",
            "contacto",
        ]


# ─── CRUD Entidades ───────────────────────────────────────

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


# ─── Detalle Entidad ──────────────────────────────────────

class EntidadDetalleView(SoloAdminMixin, DetailView):
    model = Entidad
    template_name = "users/entidad_detalle.html"
    context_object_name = "entidad"


# ─── Toggle Activo Entidad ────────────────────────────────

@login_required
def entidad_toggle(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)

    if request.user.is_superuser:
        entidad.is_active = not entidad.is_active
        entidad.save()

    return redirect("entidades_lista")


# ─── SAQ ──────────────────────────────────────────────────

@login_required
def saq_view(request):
    return render(request, "users/saq.html")
