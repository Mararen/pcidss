from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Login y Dashboard
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # Recuperar contraseña
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/reset_password_confirm.html',
            success_url='/'
        ),
        name='password_reset_confirm'),

    # Usuarios: Ver + Editar + Toggle
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('usuarios/<int:pk>/', views.UsuarioDetalleView.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle, name='usuario_toggle'),

    # Entidades: Ver + Editar + Toggle
    path('entidades/', views.EntidadListView.as_view(), name='entidades_lista'),
    path('entidades/<int:pk>/', views.EntidadDetalleView.as_view(), name='entidad_detalle'),
    path('entidades/<int:pk>/editar/', views.EntidadUpdateView.as_view(), name='entidad_editar'),
    path('entidades/<int:pk>/toggle/', views.entidad_toggle, name='entidad_toggle'),

    # SAQ
    path('saq/', views.saq_view, name='saq'),
]
