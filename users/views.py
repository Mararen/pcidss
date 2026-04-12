import os
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.db.models import Q
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import (
    Entidad, TipoSAQ, SeccionSAQ,
    PreguntaSAQ, PreguntaEnSeccion,
    PreguntaPreTest, RespuestaPreTest
)


# ─── AUTH ────────────────────────────────────────────────

def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user:
            login(request, user)

            if request.POST.get("remember"):
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)

            request.session.modified = True
            print(request.POST)
            return redirect("dashboard")

        return render(request, "users/login.html", {
            "error": "Credenciales incorrectas"
        })

    return render(request, "users/login.html")

@login_required
@permission_required('users.ver_dashboard', raise_exception=True)
def dashboard(request):
    user = request.user

    entidad_activa = Entidad.objects.filter(
        usuario=user,
        is_active=True
    ).exists()
    
    context = {
        "mod_usuarios": user.has_perm("users.ver_usuarios"),
        "mod_entidades": user.has_perm("users.ver_entidades"),
        "mod_saq": user.has_perm("users.ver_saq"),
        "mod_pretest": user.has_perm("users.usar_pretest"),
        "mod_evidencias": user.has_perm("users.ver_evidencias"),
        "mod_renovacion": user.has_perm("users.gestionar_renovacion"),
        
        "entidad_activa": entidad_activa,
    }

    return render(request, "users/dashboard.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")


# ─── PASSWORD ────────────────────────────────────────────

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
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': os.environ.get('BREVO_API_KEY'),
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': {'name': 'PCI Cert Pro', 'email': 'pcicertpro@outlook.com'},
                    'to': [{'email': email}],
                    'subject': 'Restablecer contraseña',
                    'textContent': f'Restablece tu contraseña:\n\n{reset_link}',
                }
            )

        except User.DoesNotExist:
            pass

        message = 'Si el correo existe, recibirás un enlace.'

    return render(request, 'users/forgot_password.html', {'message': message})


# ─── USUARIOS ────────────────────────────────────────────

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
        qs = User.objects.all().order_by("-date_joined")
        search = self.request.GET.get("buscar")

        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        return qs


class UsuarioDetalleView(PermissionRequiredMixin, DetailView):
    permission_required = "users.ver_usuarios"
    model = User
    template_name = "users/usuarios_detalle.html"
    context_object_name = "usuario"


class UsuarioCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "users.gestionar_usuarios"
    model = User
    form_class = UsuarioCreateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")


class UsuarioUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_usuarios"
    model = User
    form_class = UsuarioUpdateForm
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_lista")


@login_required
@permission_required('users.gestionar_usuarios', raise_exception=True)
def usuario_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    return redirect("usuarios_lista")


# ─── ENTIDADES ───────────────────────────────────────────

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
        qs = Entidad.objects.select_related("usuario").order_by("-fecha_modificacion")
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


class EntidadUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.gestionar_entidades"
    model = Entidad
    form_class = EntidadForm
    template_name = "users/entidades_form.html"
    success_url = reverse_lazy("entidades_lista")


@login_required
@permission_required('users.gestionar_entidades', raise_exception=True)
def entidad_toggle(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)
    entidad.is_active = not entidad.is_active
    entidad.save()
    return redirect("entidades_lista")


# ─── SAQ ────────────────────────────────────────────────

@login_required
@permission_required('users.ver_saq', raise_exception=True)
def saq_lista(request):
    return render(request, "users/saq_lista.html", {
        "tipos": TipoSAQ.objects.all()
    })


@login_required
@permission_required('users.ver_saq', raise_exception=True)
def saq_editor(request, tipo_pk, seccion_pk=None):
    tipo = get_object_or_404(TipoSAQ, pk=tipo_pk)
    secciones = tipo.secciones.order_by("orden")

    if seccion_pk:
        seccion_activa = get_object_or_404(SeccionSAQ, pk=seccion_pk)
    else:
        seccion_activa = secciones.first()
        if seccion_activa:
            return redirect("saq_editor_seccion", tipo_pk=tipo_pk, seccion_pk=seccion_activa.pk)

    preguntas = PreguntaEnSeccion.objects.filter(
        seccion=seccion_activa
    ).select_related("pregunta").order_by("orden") if seccion_activa else []

    return render(request, "users/saq_editor.html", {
        "tipo": tipo,
        "secciones": secciones,
        "seccion_activa": seccion_activa,
        "preguntas": preguntas,
    })


@login_required
@permission_required('users.editar_saq', raise_exception=True)
@require_POST
def saq_pregunta_crear(request, tipo_pk, seccion_pk):
    seccion = get_object_or_404(SeccionSAQ, pk=seccion_pk)
    texto = request.POST.get("texto", "").strip()
    referencia = request.POST.get("referencia_pci", "").strip()

    if texto:
        pregunta = PreguntaSAQ.objects.create(
            texto=texto,
            referencia_pci=referencia
        )
        orden = PreguntaEnSeccion.objects.filter(seccion=seccion).count() + 1
        PreguntaEnSeccion.objects.create(
            pregunta=pregunta,
            seccion=seccion,
            orden=orden
        )
        return JsonResponse({"success": True})

    return JsonResponse({"success": False})


@login_required
@permission_required('users.editar_saq', raise_exception=True)
@require_POST
def saq_pregunta_eliminar(request, tipo_pk, seccion_pk, pregunta_pk):
    pes = get_object_or_404(PreguntaEnSeccion, pk=pregunta_pk)
    pes.delete()
    return JsonResponse({"success": True})


# ─── PRETEST ─────────────────────────────────────────────

@login_required
def pretest_home(request):

    if not (request.user.is_superuser or request.user.has_perm('users.usar_pretest')):
        return redirect("dashboard")

    entidad_activa = Entidad.objects.filter(
        usuario=request.user,
        is_active=True
    ).exists()

    return render(request, "users/pretest_home.html", {
        "entidad_activa": entidad_activa
    })

@login_required
@permission_required('users.usar_pretest', raise_exception=True)
def pretest(request):

    entidad = Entidad.objects.filter(
        usuario=request.user,
        is_active=True
    ).first()

    if not entidad:
        logout(request)
        return redirect("login")

    preguntas = PreguntaPreTest.objects.all().order_by('numero')

    if request.method == "POST":
        for p in preguntas:
            val = request.POST.get(f"p_{p.id}")
            if val:
                RespuestaPreTest.objects.update_or_create(
                    usuario=request.user,
                    pregunta=p,
                    defaults={"respuesta": val}
                )
        return redirect("pretest_resultado")

    return render(request, "users/pretest.html", {
        "preguntas": preguntas
    })

@login_required
@permission_required('users.usar_pretest', raise_exception=True)
def pretest_resultado(request):

    entidad = Entidad.objects.filter(
        usuario=request.user,
        is_active=True
    ).first()

    if not entidad:
        logout(request)
        return redirect("login")

    respuestas = RespuestaPreTest.objects.filter(
        usuario=request.user
    ).select_related("pregunta")

    total = respuestas.count()
    si_count = respuestas.filter(respuesta="SI").count()
    no_count = respuestas.filter(respuesta="NO").count()

    saq_scores = {}
    for r in respuestas:
        if r.respuesta == "SI":
            saq = r.pregunta.saq_destino
            saq_scores[saq] = saq_scores.get(saq, 0) + 1

    recomendacion = max(saq_scores, key=saq_scores.get) if saq_scores else "No determinado"

    return render(request, "users/pretest_resultado.html", {
        "total": total,
        "si": si_count,
        "no": no_count,
        "recomendacion": recomendacion,
        "saq_scores": saq_scores,
    })