from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # ─── Login / Dashboard ────────────────────────────────
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # ─── Password reset ───────────────────────────────────
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/reset_password_confirm.html',
            success_url='/'
        ),
        name='password_reset_confirm'),

    # ─── Usuarios ─────────────────────────────────────────
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/', views.UsuarioDetalleView.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle, name='usuario_toggle'),

    # ─── Entidades ────────────────────────────────────────
    path('entidades/', views.EntidadListView.as_view(), name='entidades_lista'),
    path('entidades/nueva/', views.EntidadCreateView.as_view(), name='entidad_crear'),
    path('entidades/<int:pk>/', views.EntidadDetalleView.as_view(), name='entidad_detalle'),
    path('entidades/<int:pk>/editar/', views.EntidadUpdateView.as_view(), name='entidad_editar'),
    path('entidades/<int:pk>/toggle/', views.entidad_toggle, name='entidad_toggle'),

    # ─── SAQ — Lista de tipos ─────────────────────────────
    path('saq/', views.saq_lista, name='saq_lista'),
    path('saq/nuevo/', views.saq_tipo_crear, name='saq_tipo_crear'),

    # ─── SAQ — Detalle (secciones + preguntas) ────────────
    path('saq/<int:tipo_pk>/', views.saq_detalle, name='saq_detalle'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/', views.saq_detalle, name='saq_detalle_seccion'),
    path('saq/<int:tipo_pk>/editar/', views.saq_tipo_editar, name='saq_tipo_editar'),

    # ─── SAQ — Secciones ──────────────────────────────────
    path('saq/<int:tipo_pk>/seccion/nueva/', views.saq_seccion_crear, name='saq_seccion_crear'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/editar/', views.saq_seccion_editar, name='saq_seccion_editar'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/eliminar/', views.saq_seccion_eliminar, name='saq_seccion_eliminar'),

    # ─── SAQ — Preguntas ──────────────────────────────────
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/pregunta/nueva/', views.saq_pregunta_agregar, name='saq_pregunta_agregar'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/pregunta/<int:pregunta_pk>/editar/', views.saq_pregunta_editar, name='saq_pregunta_editar'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/pregunta/<int:pregunta_pk>/eliminar/', views.saq_pregunta_eliminar, name='saq_pregunta_eliminar'),
]
