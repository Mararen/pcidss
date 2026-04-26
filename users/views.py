import os
import requests
import urllib.parse
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Q, Max

from .models import (
    Entidad,
    ConfiguracionGeneral,
    PoliticaSeguridad,
    NotificacionConfig,
    LogAuditoria,
)

# ─────────────────────────────────────────────
# LOGS
# ─────────────────────────────────────────────

def registrar_log(request, accion, modulo, descripcion, target_user=None):
    LogAuditoria.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        target_user=target_user,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        ip=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────

def login_view(request):
    recaptcha_site_key = os.environ.get('RECAPTCHA_PUBLIC_KEY')

    if request.method == "POST":
        # Validar reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': os.environ.get('RECAPTCHA_PRIVATE_KEY'),
            'response': recaptcha_response,
        })
        if not r.json().get('success'):
            return render(request, "users/login.html", {
                "error": "Verifica que no eres un robot.",
                "recaptcha_site_key": recaptcha_site_key,
            })

        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user:
            login(request, user)
            registrar_log(request, "LOGIN", "AUTH", f"{user.username} login")
            return redirect("dashboard")

        return render(request, "users/login.html", {
            "error": "Credenciales incorrectas",
            "recaptcha_site_key": recaptcha_site_key,
        })

    return render(request, "users/login.html", {
        "recaptcha_site_key": recaptcha_site_key,
    })


@login_required
def logout_view(request):
    registrar_log(request, "LOGOUT", "AUTH", "logout")
    logout(request)
    return redirect("login")


@login_required
@permission_required('users.ver_dashboard', raise_exception=True)
def dashboard(request):
    return render(request, "users/dashboard.html")


# ─────────────────────────────────────────────
# PASSWORD
# ─────────────────────────────────────────────

def forgot_password(request):
    message = None

    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            link = request.build_absolute_uri(
                f'/reset-password/{uid}/{token}/'
            )

            requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': os.environ.get('BREVO_API_KEY'),
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': {'name': 'PCI Cert Pro', 'email': 'pcicertpro@outlook.com'},
                    'to': [{'email': email}],
                    'subject': 'Reset password',
                    'textContent': link,
                }
            )

        except User.DoesNotExist:
            pass

        message = "Si el correo existe, recibirás un enlace."

    return render(request, 'users/forgot_password.html', {'message': message})


# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def configuracion_general(request):
    config, _ = ConfiguracionGeneral.objects.get_or_create(id=1)

    if request.method == "POST":
        config.nombre_sistema = request.POST.get("nombre")
        config.tiempo_sesion = int(request.POST.get("tiempo"))
        config.idioma = request.POST.get("idioma")
        config.zona_horaria = request.POST.get("zona")
        config.save()
        return JsonResponse({"success": True})

    return render(request, "users/configuracion/general.html", {"config": config})


@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def configuracion_seguridad(request):
    return render(request, "users/configuracion/seguridad.html")


@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def configuracion_notificaciones(request):
    return render(request, "users/configuracion/notificaciones.html")


# ─────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────

class UsuarioCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]


class UsuarioListView(PermissionRequiredMixin, ListView):
    permission_required = "users.ver_usuarios"
    model = User
    template_name = "users/usuarios_lista.html"
    context_object_name = "usuarios"
    paginate_by = 5

    def get_queryset(self):
        qs = (
            User.objects
            .prefetch_related("groups")
            .annotate(
                ultima_modificacion=Max("audit_events_as_target__fecha")
            )
            .order_by("-date_joined")
        )

        search = self.request.GET.get("buscar")

        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        for user in qs:
            if user.is_superuser or user.groups.filter(name="Administrador Global").exists():
                user.rol_display = "Administrador Global"
            else:
                grupo = user.groups.first()
                user.rol_display = grupo.name if grupo else "Usuario Estándar"

        return qs


class UsuarioDetalleView(PermissionRequiredMixin, DetailView):
    permission_required = "users.ver_usuarios"
    model = User
    template_name = "users/usuarios_detalle.html"
    context_object_name = "usuario"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["ultima_modificacion"] = LogAuditoria.objects.filter(
            target_user=self.object
        ).aggregate(Max("fecha"))["fecha__max"]

        return context


class UsuarioCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "users.gestionar_usuarios"
    model = User
    form_class = UsuarioCreateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        response = super().form_valid(form)

        registrar_log(
            self.request,
            "CREATE",
            "USUARIOS",
            f"Usuario creado: {self.object.username}",
            target_user=self.object
        )

        return response


class UsuarioUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_usuarios"
    model = User
    form_class = UsuarioUpdateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        user = form.save()

        registrar_log(
            self.request,
            "UPDATE",
            "USUARIOS",
            f"Usuario actualizado: {user.username}",
            target_user=user
        )

        return super().form_valid(form)


@login_required
@permission_required('users.gestionar_usuarios', raise_exception=True)
def usuario_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()

    registrar_log(
        request,
        "UPDATE",
        "USUARIOS",
        f"Usuario {'activado' if user.is_active else 'desactivado'}: {user.username}",
        target_user=user
    )

    return redirect("usuarios_lista")


# ─────────────────────────────────────────────
# ENTIDADES
# ─────────────────────────────────────────────

class EntidadForm(forms.ModelForm):
    class Meta:
        model = Entidad
        fields = ["usuario", "nombre_empresa", "dba", "email", "sitio_web", "contacto"]


class EntidadListView(PermissionRequiredMixin, ListView):
    permission_required = "users.ver_entidades"
    model = Entidad
    template_name = "users/entidades_lista.html"
    context_object_name = "entidades"
    paginate_by = 5

    def get_queryset(self):
        qs = (
            Entidad.objects
            .select_related("usuario", "creado_por", "modificado_por")
            .order_by("-fecha_modificacion")
        )

        search = self.request.GET.get("buscar")

        if search:
            qs = qs.filter(
                Q(nombre_empresa__icontains=search) |
                Q(dba__icontains=search) |
                Q(email__icontains=search) |
                Q(contacto__icontains=search)
            )

        return qs
        
class EntidadDetalleView(PermissionRequiredMixin, DetailView):
    permission_required = "users.ver_entidades"
    model = Entidad
    template_name = "users/entidades_detalle.html"
    context_object_name = "entidad"


class EntidadCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "users.gestionar_entidades"
    model = Entidad
    form_class = EntidadForm
    template_name = "users/entidades_form.html"
    success_url = reverse_lazy("entidades_lista")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.creado_por = self.request.user
        obj.modificado_por = self.request.user
        obj.save()
        return super().form_valid(form)


class EntidadUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_entidades"
    model = Entidad
    form_class = EntidadForm
    template_name = "users/entidades_form.html"
    success_url = reverse_lazy("entidades_lista")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return super().form_valid(form)

@login_required
@permission_required('users.gestionar_entidades', raise_exception=True)
def entidad_toggle(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)
    entidad.is_active = not entidad.is_active
    entidad.save()
    return redirect("entidades_lista")