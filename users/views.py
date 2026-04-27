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
    LogAuditoria,
    ConfiguracionGeneral,
    PoliticaSeguridad,
    NotificacionConfig,
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
        # Validar reCAPTCHA v3
        recaptcha_response = request.POST.get('g-recaptcha-response')
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': os.environ.get('RECAPTCHA_PRIVATE_KEY'),
            'response': recaptcha_response,
        })
        result = r.json()
        if not result.get('success') or result.get('score', 0) < 0.5:
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
    notificaciones = NotificacionConfig.objects.filter(activo=True)
    return render(request, "users/dashboard.html", {"notificaciones": notificaciones})
    
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

    if request.method == "POST":                          # ← debe estar dentro de la función
        config.nombre_sistema = request.POST.get("nombre")
        config.tiempo_sesion  = int(request.POST.get("tiempo"))
        config.idioma         = request.POST.get("idioma")
        config.zona_horaria   = request.POST.get("zona")

        if "logo" in request.FILES:
            config.logo = request.FILES["logo"]

        config.save()
        registrar_log(request, "UPDATE", "Configuración", "Actualizó configuración general")
        return JsonResponse({"success": True})

    return render(request, "users/configuracion/general.html", {"config": config})


@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def configuracion_seguridad(request):
    politica, _ = PoliticaSeguridad.objects.get_or_create(
        id=1,
        defaults={
            "dias_vigencia":     90,
            "intentos_fallidos": 5,
        }
    )

    if request.method == "POST":
        # Obtener valores con defaults seguros
        try:
            longitud = int(request.POST.get("longitud", 8))
            dias     = int(request.POST.get("dias", 90))
            intentos = int(request.POST.get("intentos", 5))
        except ValueError:
            return JsonResponse({"error": "Los valores deben ser numéricos."}, status=400)

        # Validación de rangos
        if not (6 <= longitud <= 32):
            return JsonResponse({"error": "La longitud debe estar entre 6 y 32 caracteres."}, status=400)
        if not (1 <= dias <= 365):
            return JsonResponse({"error": "Los días de vigencia deben estar entre 1 y 365."}, status=400)
        if not (1 <= intentos <= 10):
            return JsonResponse({"error": "Los intentos fallidos deben estar entre 1 y 10."}, status=400)

        # Guardar
        politica.longitud_minima     = longitud
        politica.dias_vigencia       = dias
        politica.intentos_fallidos   = intentos
        politica.requiere_numeros    = "numeros"    in request.POST
        politica.requiere_mayusculas = "mayusculas" in request.POST
        politica.requiere_simbolos   = "simbolos"   in request.POST
        politica.save()
        registrar_log(request, "UPDATE", "Configuración", "Actualizó política de seguridad")
        return JsonResponse({"success": True})

    return render(request, "users/configuracion/seguridad.html", {"politica": politica})

@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def configuracion_notificaciones(request):
    if request.method == "POST":
        tipo   = request.POST.get("tipo")
        dias   = request.POST.get("dias")
        canal  = request.POST.get("canal")
        estilo = request.POST.get("estilo")

        obj, created = NotificacionConfig.objects.update_or_create(
            tipo=tipo,
            defaults={"dias_antes": dias, "canal": canal, "estilo": estilo, "activo": True}
        )
        registrar_log(request, "CREATE" if created else "UPDATE",
                      "Configuración", f"Notificación '{tipo}' configurada")
        return JsonResponse({"success": True})

    notificaciones = NotificacionConfig.objects.all() 
    return render(request, "users/configuracion/notificaciones.html",
                  {"notificaciones": notificaciones})

@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def notificacion_editar(request, pk):
    notif = get_object_or_404(NotificacionConfig, pk=pk)

    if request.method == "POST":
        notif.tipo      = request.POST.get("tipo")
        notif.dias_antes = int(request.POST.get("dias"))
        notif.canal     = request.POST.get("canal")
        notif.estilo    = request.POST.get("estilo")
        notif.save()
        registrar_log(request, "UPDATE", "Configuración", f"Notificación '{notif.tipo}' editada")
        return JsonResponse({"success": True})

    return JsonResponse({
        "tipo":      notif.tipo,
        "dias":      notif.dias_antes,
        "canal":     notif.canal,
        "estilo":    notif.estilo,
    })

@login_required
@permission_required('users.gestionar_configuracion', raise_exception=True)
def notificacion_eliminar(request, pk):
    if request.method == "POST":
        notif = get_object_or_404(NotificacionConfig, pk=pk)
        notif.delete()
        registrar_log(request, "DELETE", "Configuración", f"Notificación '{notif.tipo}' eliminada")
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método no permitido"}, status=405)

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

    def clean_first_name(self):
        valor = self.cleaned_data.get("first_name", "")
        if any(c.isdigit() for c in valor):
            raise forms.ValidationError("El nombre no puede contener números.")
        return valor.strip()

    def clean_last_name(self):
        valor = self.cleaned_data.get("last_name", "")
        if any(c.isdigit() for c in valor):
            raise forms.ValidationError("El apellido no puede contener números.")
        return valor.strip()

    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        return email.lower()


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
    if request.method != "POST":
        return redirect("usuarios_lista")

    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    registrar_log(
        request, "UPDATE", "USUARIOS",
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

    def clean_nombre_empresa(self):
        """Nombre de empresa: mínimo 2 caracteres."""
        valor = self.cleaned_data.get("nombre_empresa", "").strip()
        if len(valor) < 2:
            raise forms.ValidationError("El nombre de la empresa debe tener al menos 2 caracteres.")
        return valor

    def clean_email(self):
        """Email obligatorio y en minúsculas."""
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        return email.lower()

    def clean_contacto(self):
        """Contacto: solo letras y espacios, sin números."""
        valor = self.cleaned_data.get("contacto", "").strip()
        if any(c.isdigit() for c in valor):
            raise forms.ValidationError("El nombre del contacto no puede contener números.")
        return valor


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
    if request.method != "POST":
        return redirect("entidades_lista")

    entidad = get_object_or_404(Entidad, pk=pk)
    entidad.is_active = not entidad.is_active
    entidad.save()
    registrar_log(
        request, "UPDATE", "ENTIDADES",
        f"Entidad {'activada' if entidad.is_active else 'desactivada'}: {entidad.nombre_empresa}"
    )
    return redirect("entidades_lista")