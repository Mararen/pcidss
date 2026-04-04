from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # AUTH
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # PASSWORD
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/reset_password_confirm.html',
             success_url='/'
         ),
         name='password_reset_confirm'),

    # USUARIOS
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/', views.UsuarioDetalleView.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle, name='usuario_toggle'),

    # ENTIDADES
    path('entidades/', views.EntidadListView.as_view(), name='entidades_lista'),
    path('entidades/nueva/', views.EntidadCreateView.as_view(), name='entidad_crear'),
    path('entidades/<int:pk>/editar/', views.EntidadUpdateView.as_view(), name='entidad_editar'),
    path('entidades/<int:pk>/toggle/', views.entidad_toggle, name='entidad_toggle'),

    # SAQ

    path('saq/', views.saq_lista, name='saq_lista'),
    path('saq/<int:tipo_pk>/', views.saq_detalle, name='saq_detalle'),
    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/', views.saq_detalle_seccion, name='saq_detalle_seccion'),

    # AJAX
    path('saq/<int:tipo_pk>/seccion/crear/', views.saq_seccion_crear, name='saq_seccion_crear'),

    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/pregunta/ajax/crear/',
     views.saq_pregunta_ajax_crear,
     name='saq_pregunta_ajax_crear'),

    path('saq/<int:tipo_pk>/seccion/<int:seccion_pk>/pregunta/<int:pregunta_pk>/eliminar/',
     views.saq_pregunta_eliminar,
     name='saq_pregunta_eliminar'),
]