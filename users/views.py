import os
import re
import requests
import urllib.parse
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Q, Max
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import (
    Entidad,
    LogAuditoria,
    ConfiguracionGeneral,
    PoliticaSeguridad,
    NotificacionConfig,
    PerfilSeguridad,
    Evidencia,
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

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # reCAPTCHA v3.
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

        # Verifica si el usuario existe.
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, "users/login.html", {
                "error": "Credenciales incorrectas.",
                "recaptcha_site_key": recaptcha_site_key,
            })

        # Obtiene o crea el perfil de seguridad.
        perfil, _ = PerfilSeguridad.objects.get_or_create(usuario=user_obj)

        # Bloqueo de cuenta por demasiados intentos.
        if perfil.esta_bloqueado():
            minutos  = perfil.segundos_restantes() // 60
            segundos = perfil.segundos_restantes() % 60
            return render(request, "users/login.html", {
                "error": (
                    f"Cuenta bloqueada por demasiados intentos fallidos. "
                    f"Intenta de nuevo en {minutos}m {segundos}s."
                ),
                "recaptcha_site_key": recaptcha_site_key,
            })

        # Autenticación.
        user = authenticate(request, username=username, password=password)

        if user is None:
            perfil.registrar_intento_fallido(minutos_bloqueo=30)
            registrar_log(request, "LOGIN", "AUTH",
                          f"Intento fallido para usuario: {username}")

            politica     = PoliticaSeguridad.objects.first()
            max_intentos = politica.intentos_fallidos if politica else 5
            restantes    = max(0, max_intentos - perfil.intentos_fallidos)

            if perfil.esta_bloqueado():
                error_msg = ("Demasiados intentos fallidos. "
                             "Tu cuenta ha sido bloqueada por 30 minutos.")
            else:
                error_msg = (f"Credenciales incorrectas. "
                             f"Intentos restantes antes del bloqueo: {restantes}.")

            return render(request, "users/login.html", {
                "error": error_msg,
                "recaptcha_site_key": recaptcha_site_key,
            })

        # Login exitoso.
        perfil.resetear_intentos()
        login(request, user)
        registrar_log(request, "LOGIN", "AUTH", f"{user.username} inició sesión")

        # Contraseña vencida, solicitar cambio.
        if perfil.contrasena_vencida() or perfil.forzar_cambio:
            return redirect("cambiar_contrasena")

        return redirect("dashboard")

    return render(request, "users/login.html", {
        "recaptcha_site_key": recaptcha_site_key,
    })


# ─────────────────────────────────────────────
# LOGOUT CON CONFIRMACIÓN
# ─────────────────────────────────────────────

@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "POST":
        registrar_log(request, "LOGOUT", "AUTH", f"{request.user.username} cerró sesión")
        logout(request)
        return redirect("login")
    return render(request, "users/logout_confirm.html")


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@login_required
@permission_required('users.ver_dashboard', raise_exception=True)
def dashboard(request):
    from saq.models import PreTest
    from helpdesk.models import Ticket

    total_entidades = Entidad.objects.filter(is_active=True).count()
    total_pretests  = PreTest.objects.filter(estado='completado').count()
    total_tickets   = Ticket.objects.filter(estado='abierto').count()
    total_usuarios  = User.objects.filter(is_active=True).count()

    ultimos_accesos = LogAuditoria.objects.filter(
        accion='LOGIN'
    ).select_related('usuario').order_by('-fecha')[:5]

    ultimos_tickets = Ticket.objects.select_related(
        'usuario', 'entidad', 'categoria'
    ).order_by('-fecha_creacion')[:5]

    notificaciones = NotificacionConfig.objects.filter(activo=True)

    return render(request, "users/dashboard.html", {
        "total_entidades": total_entidades,
        "total_pretests":  total_pretests,
        "total_tickets":   total_tickets,
        "total_usuarios":  total_usuarios,
        "ultimos_accesos": ultimos_accesos,
        "ultimos_tickets": ultimos_tickets,
        "notificaciones":  notificaciones,
    })


# ─────────────────────────────────────────────
# CAMBIO DE CONTRASEÑA FORZADO
# ─────────────────────────────────────────────

@login_required
def cambiar_contrasena(request):
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    perfil   = PerfilSeguridad.objects.get_or_create(usuario=request.user)[0]
    politica = PoliticaSeguridad.objects.first()  # ← agrega esta línea
    error    = None

    if request.method == "POST":
        actual  = request.POST.get("actual", "")
        nueva   = request.POST.get("nueva", "")
        repetir = request.POST.get("repetir", "")

        if not request.user.check_password(actual):
            error = "La contraseña actual es incorrecta."
        elif nueva != repetir:
            error = "Las contraseñas nuevas no coinciden."
        else:
            try:
                validate_password(nueva, user=request.user)
            except ValidationError as e:
                error = " ".join(e.messages)

        if not error:
            request.user.set_password(nueva)
            request.user.save()
            from django.utils import timezone as tz
            perfil.contrasena_desde = tz.now()
            perfil.forzar_cambio    = False
            perfil.save(update_fields=["contrasena_desde", "forzar_cambio"])
            registrar_log(request, "UPDATE", "AUTH",
                          f"{request.user.username} cambió su contraseña")
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            return redirect("dashboard")

    return render(request, "users/cambiar_contrasena.html", {
        "error":    error,
        "perfil":   perfil,
        "politica": politica,
    })

# ─────────────────────────────────────────────
# PASSWORD RECOVERY
# ─────────────────────────────────────────────

def forgot_password(request):
    message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user  = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            link  = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')
            requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': os.environ.get('BREVO_API_KEY'),
                    'Content-Type': 'application/json',
                },
                json={
                    'sender':      {'name': 'PCI Cert Pro', 'email': 'pcicertpro@outlook.com'},
                    'to':          [{'email': email}],
                    'subject':     'Reset password',
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
        id=1, defaults={"dias_vigencia": 90, "intentos_fallidos": 5}
    )
    if request.method == "POST":
        try:
            longitud = int(request.POST.get("longitud", 8))
            dias     = int(request.POST.get("dias", 90))
            intentos = int(request.POST.get("intentos", 5))
        except ValueError:
            return JsonResponse({"error": "Los valores deben ser numéricos."}, status=400)

        if not (6 <= longitud <= 32):
            return JsonResponse({"error": "Longitud entre 6 y 32."}, status=400)
        if not (1 <= dias <= 365):
            return JsonResponse({"error": "Días de vigencia entre 1 y 365."}, status=400)
        if not (1 <= intentos <= 10):
            return JsonResponse({"error": "Intentos entre 1 y 10."}, status=400)

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
        notif.tipo       = request.POST.get("tipo")
        notif.dias_antes = int(request.POST.get("dias"))
        notif.canal      = request.POST.get("canal")
        notif.estilo     = request.POST.get("estilo")
        notif.save()
        registrar_log(request, "UPDATE", "Configuración", f"Notificación '{notif.tipo}' editada")
        return JsonResponse({"success": True})
    return JsonResponse({"tipo": notif.tipo, "dias": notif.dias_antes,
                         "canal": notif.canal, "estilo": notif.estilo})


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
# USUARIOS — FORMULARIOS
# ─────────────────────────────────────────────

# Solo letras (con acentos), espacios y guiones
PATRON_SOLO_LETRAS = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s\-']+$")


class UsuarioCreateForm(UserCreationForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        help_text="Asigna un rol al usuario."
    )

    class Meta:
        model  = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text   = "3–100 caracteres. Solo letras, números y: @ . + - _"
        self.fields["first_name"].help_text = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["last_name"].help_text  = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["email"].help_text      = "Debe ser único en el sistema. Ej: usuario@empresa.com"
        self.fields["password1"].help_text  = "Mínimo 8 caracteres con mayúsculas, números y símbolos."
        self.fields["password2"].help_text  = "Repite la contraseña para confirmar."

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("El nombre de usuario es obligatorio.")
        if len(username) < 3:
            raise forms.ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(username) > 100:
            raise forms.ValidationError("El nombre de usuario no puede superar 100 caracteres.")
        if not re.match(r'^[\w.@+\-]+$', username):
            raise forms.ValidationError(
                "Solo se permiten letras, números y los caracteres: @ . + - _"
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_first_name(self):
        valor = self.cleaned_data.get("first_name", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El nombre no puede superar 100 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return valor

    def clean_last_name(self):
        valor = self.cleaned_data.get("last_name", "").strip()
        if not valor:
            raise forms.ValidationError("El apellido es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El apellido debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El apellido no puede superar 100 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("El apellido solo puede contener letras y espacios.")
        return valor

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise forms.ValidationError("Ingresa un correo electrónico válido.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text   = "3–100 caracteres. Solo letras, números y: @ . + - _"
        self.fields["first_name"].help_text = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["last_name"].help_text  = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["email"].help_text      = "Debe ser único en el sistema. Ej: usuario@empresa.com"

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("El nombre de usuario es obligatorio.")
        if len(username) < 3:
            raise forms.ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(username) > 100:
            raise forms.ValidationError("El nombre de usuario no puede superar 100 caracteres.")
        if not re.match(r'^[\w.@+\-]+$', username):
            raise forms.ValidationError(
                "Solo se permiten letras, números y los caracteres: @ . + - _"
            )
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_first_name(self):
        valor = self.cleaned_data.get("first_name", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El nombre no puede superar 100 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return valor

    def clean_last_name(self):
        valor = self.cleaned_data.get("last_name", "").strip()
        if not valor:
            raise forms.ValidationError("El apellido es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El apellido debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El apellido no puede superar 100 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("El apellido solo puede contener letras y espacios.")
        return valor

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise forms.ValidationError("Ingresa un correo electrónico válido.")
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email


# ─────────────────────────────────────────────
# USUARIOS — VISTAS
# ─────────────────────────────────────────────

class UsuarioListView(PermissionRequiredMixin, ListView):
    permission_required = "users.ver_usuarios"
    model               = User
    template_name       = "users/usuarios_lista.html"
    context_object_name = "usuarios"
    paginate_by         = 5

    def get_queryset(self):
        qs = (
            User.objects
            .prefetch_related("groups")
            .annotate(ultima_modificacion=Max("audit_events_as_target__fecha"))
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
    model               = User
    template_name       = "users/usuarios_detalle.html"
    context_object_name = "usuario"

    def has_permission(self):
        # Permite acceso si el usuario está viendo su propio perfil
        if self.request.user.pk == self.kwargs.get("pk"):
            return True
        return super().has_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ultima_modificacion"] = LogAuditoria.objects.filter(
            target_user=self.object
        ).aggregate(Max("fecha"))["fecha__max"]
        return context

class UsuarioCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "users.gestionar_usuarios"
    model               = User
    form_class          = UsuarioCreateForm
    template_name       = "users/usuarios_form.html"
    success_url         = reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        rol = form.cleaned_data.get("rol")
        if rol:
            self.object.groups.set([rol])
        registrar_log(self.request, "CREATE", "USUARIOS",
                      f"Usuario creado: {self.object.username}", target_user=self.object)
        return response

class UsuarioSelfUpdateForm(forms.ModelForm):
    """Formulario para que el usuario edite su propio perfil sin cambiar rol ni estado."""
    class Meta:
        model  = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text   = "3–100 caracteres. Solo letras, números y: @ . + - _"
        self.fields["first_name"].help_text = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["last_name"].help_text  = "Solo letras y espacios. Mínimo 2 caracteres."
        self.fields["email"].help_text      = "Debe ser único en el sistema."

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("El nombre de usuario es obligatorio.")
        if len(username) < 3:
            raise forms.ValidationError("Mínimo 3 caracteres.")
        if not re.match(r'^[\w.@+\-]+$', username):
            raise forms.ValidationError("Solo letras, números y: @ . + - _")
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_first_name(self):
        valor = self.cleaned_data.get("first_name", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("Mínimo 2 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("Solo letras y espacios.")
        return valor

    def clean_last_name(self):
        valor = self.cleaned_data.get("last_name", "").strip()
        if not valor:
            raise forms.ValidationError("El apellido es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("Mínimo 2 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("Solo letras y espacios.")
        return valor

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise forms.ValidationError("Correo inválido.")
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email


class UsuarioUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_usuarios"
    model               = User
    form_class          = UsuarioUpdateForm
    template_name       = "users/usuarios_form.html"
    success_url         = reverse_lazy("usuarios_lista")

    def has_permission(self):
        # El usuario siempre puede editar su propio perfil
        if self.request.user.pk == self.kwargs.get("pk"):
            return True
        return super().has_permission()

    def get_form_class(self):
        # Si está editando su propio perfil, usa el formulario sin rol ni estado
        if self.request.user.pk == self.kwargs.get("pk"):
            return UsuarioSelfUpdateForm
        return UsuarioUpdateForm

    def get_success_url(self):
        # Redirige al propio perfil si se estaba editando a sí mismo
        if self.request.user.pk == self.kwargs.get("pk"):
            return reverse_lazy("usuario_detalle", kwargs={"pk": self.request.user.pk})
        return reverse_lazy("usuarios_lista")

    def form_valid(self, form):
        user = form.save()
        registrar_log(self.request, "UPDATE", "USUARIOS",
                      f"Usuario actualizado: {user.username}", target_user=user)
        return super().form_valid(form)

@login_required
@permission_required('users.gestionar_usuarios', raise_exception=True)
def usuario_toggle(request, pk):
    if request.method != "POST":
        return redirect("usuarios_lista")
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        return redirect("usuarios_lista")
    if user.is_superuser:
        return redirect("usuarios_lista")
    user.is_active = not user.is_active
    user.save()
    registrar_log(
        request, "UPDATE", "USUARIOS",
        f"Usuario {'activado' if user.is_active else 'desactivado'}: {user.username}",
        target_user=user
    )
    return redirect("usuarios_lista")

# ─────────────────────────────────────────────
# ENTIDADES — FORMULARIO
# ─────────────────────────────────────────────

class EntidadForm(forms.ModelForm):
    class Meta:
        model  = Entidad
        fields = ["usuario", "nombre_empresa", "dba", "email", "sitio_web", "contacto"]

    def __init__(self, *args, **kwargs):                          # ← DENTRO de la clase
        super().__init__(*args, **kwargs)
        self.fields["nombre_empresa"].help_text = "Razón social completa. Mínimo 2 caracteres. Debe ser única."
        self.fields["dba"].help_text            = "Nombre comercial o marca. Mínimo 2 caracteres."
        self.fields["email"].help_text          = "Correo de contacto principal. Ej: contacto@empresa.com"
        self.fields["sitio_web"].help_text      = "Opcional. Ej: https://empresa.com"
        self.fields["contacto"].help_text       = "Nombre del responsable. Solo letras, sin números."
        # Placeholders
        self.fields["sitio_web"].widget.attrs["placeholder"]      = "https://"
        self.fields["email"].widget.attrs["placeholder"]          = "contacto@empresa.com"
        self.fields["nombre_empresa"].widget.attrs["placeholder"] = "Ej: Empresa S.A. de C.V."
        self.fields["contacto"].widget.attrs["placeholder"]       = "Ej: Juan Pérez"

    def clean_nombre_empresa(self):                               # ← DENTRO de la clase
        valor = self.cleaned_data.get("nombre_empresa", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre de la empresa es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El nombre no puede superar 100 caracteres.")
        qs = Entidad.objects.filter(nombre_empresa__iexact=valor)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una entidad con este nombre.")
        return valor

    def clean_dba(self):
        valor = self.cleaned_data.get("dba", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre comercial (DBA) es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El DBA debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El DBA no puede superar 100 caracteres.")
        return valor

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise forms.ValidationError("Ingresa un correo electrónico válido.")
        qs = Entidad.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado en otra entidad.")
        return email

    def clean_contacto(self):
        valor = self.cleaned_data.get("contacto", "").strip()
        if not valor:
            raise forms.ValidationError("El nombre del contacto es obligatorio.")
        if len(valor) < 2:
            raise forms.ValidationError("El contacto debe tener al menos 2 caracteres.")
        if len(valor) > 100:
            raise forms.ValidationError("El contacto no puede superar 100 caracteres.")
        if not PATRON_SOLO_LETRAS.match(valor):
            raise forms.ValidationError("El contacto solo puede contener letras y espacios.")
        return valor


# ─────────────────────────────────────────────
# ENTIDADES — VISTAS
# ─────────────────────────────────────────────

class EntidadListView(PermissionRequiredMixin, ListView):
    permission_required = "users.ver_entidades"
    model               = Entidad
    template_name       = "users/entidades_lista.html"
    context_object_name = "entidades"
    paginate_by         = 5

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
    model               = Entidad
    template_name       = "users/entidades_detalle.html"
    context_object_name = "entidad"


class EntidadCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "users.gestionar_entidades"
    model               = Entidad
    form_class          = EntidadForm
    template_name       = "users/entidades_form.html"
    success_url         = reverse_lazy("entidades_lista")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.creado_por     = self.request.user
        obj.modificado_por = self.request.user
        obj.save()
        return super().form_valid(form)


class EntidadUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_entidades"
    model               = Entidad
    form_class          = EntidadForm
    template_name       = "users/entidades_form.html"
    success_url         = reverse_lazy("entidades_lista")

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
    
# ─────────────────────────────────────────────
# EVIDENCIAS FORMULARIO
# ─────────────────────────────────────────────

class EvidenciaForm(forms.ModelForm):

    class Meta:
        model = Evidencia

        fields = [
            'entidad',
            'titulo',
            'descripcion',
            'tipo',
            'archivo'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['titulo'].widget.attrs.update({
            'placeholder': 'Ej: Escaneo ASV Q1 2026'
        })

    def clean_archivo(self):

        archivo = self.cleaned_data.get(
            'archivo'
        )

        if not archivo:
            raise forms.ValidationError(
                'Debes seleccionar un archivo.'
            )

        extensiones_permitidas = [
            '.pdf',
            '.png',
            '.jpg',
            '.jpeg',
            '.docx',
            '.xlsx',
            '.zip'
        ]

        extension = os.path.splitext(
            archivo.name
        )[1].lower()

        if extension not in extensiones_permitidas:
            raise forms.ValidationError(
                'Formato no permitido.'
            )

        if archivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                'Máximo permitido: 10MB.'
            )

        return archivo
        
# ─────────────────────────────────────────────
# EVIDENCIAS LISTADO
# ─────────────────────────────────────────────

class EvidenciaListView(
    PermissionRequiredMixin,
    ListView
):

    permission_required = 'users.ver_evidencias'

    model = Evidencia

    template_name = 'users/evidencias_lista.html'

    context_object_name = 'evidencias'

    paginate_by = 10

    def get_queryset(self):

        qs = (
            Evidencia.objects
            .select_related(
                'entidad',
                'subido_por'
            )
            .filter(activa=True)
            .order_by('-fecha_subida')
        )

        buscar = self.request.GET.get(
            'buscar'
        )

        entidad = self.request.GET.get(
            'entidad'
        )

        tipo = self.request.GET.get(
            'tipo'
        )

        if buscar:

            qs = qs.filter(
                Q(titulo__icontains=buscar)
            )

        if entidad:

            qs = qs.filter(
                entidad_id=entidad
            )

        if tipo:

            qs = qs.filter(
                tipo=tipo
            )

        return qs

# ─────────────────────────────────────────────
# EVIDENCIAS CREACIÓN
# ─────────────────────────────────────────────

class EvidenciaCreateView(
    PermissionRequiredMixin,
    CreateView
):

    permission_required = 'users.gestionar_evidencias'

    model = Evidencia

    form_class = EvidenciaForm

    template_name = 'users/evidencias_form.html'

    success_url = reverse_lazy(
        'evidencias_lista'
    )

    def form_valid(self, form):

        obj = form.save(
            commit=False
        )

        obj.subido_por = self.request.user

        obj.save()

        registrar_log(
            self.request,
            'CREATE',
            'EVIDENCIAS',
            f'Evidencia subida: {obj.titulo}'
        )

        return redirect(
            self.success_url
        )
        
# ─────────────────────────────────────────────
# EVIDENCIAS ELIMINAR
# ─────────────────────────────────────────────

class EvidenciaDeleteView(
    PermissionRequiredMixin,
    DeleteView
):

    permission_required = 'users.gestionar_evidencias'

    model = Evidencia

    success_url = reverse_lazy(
        'evidencias_lista'
    )

    def delete(self, request, *args, **kwargs):

        obj = self.get_object()

        registrar_log(
            request,
            'DELETE',
            'EVIDENCIAS',
            f'Evidencia eliminada: {obj.titulo}'
        )

        # Elimina archivo físico
        if obj.archivo:
            obj.archivo.delete(save=False)

        return super().delete(
            request,
            *args,
            **kwargs
        )

# ─────────────────────────────────────────────
# EVIDENCIAS DESCARGAR
# ─────────────────────────────────────────────

@login_required
@permission_required(
    'users.ver_evidencias',
    raise_exception=True
)
def evidencia_descargar(
    request,
    pk
):

    evidencia = get_object_or_404(
        Evidencia,
        pk=pk
    )

    registrar_log(
        request,
        'DOWNLOAD',
        'EVIDENCIAS',
        f'Descarga: {evidencia.titulo}'
    )

    return FileResponse(
        evidencia.archivo.open('rb'),
        as_attachment=True,
        filename=os.path.basename(
            evidencia.archivo.name
        )
    )