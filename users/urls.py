from django.urls import path
from . import views

urlpatterns = [

    # Login y Dashboard
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # CRUD Usuarios
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_eliminar'),

    # CRUD Entidades
    path('entidades/', views.EntidadListView.as_view(), name='entidades_lista'),
    path('entidades/nueva/', views.EntidadCreateView.as_view(), name='entidad_crear'),
    path('entidades/<int:pk>/', views.EntidadDetalleView.as_view(), name='entidad_detalle'),
    path('entidades/<int:pk>/editar/', views.EntidadUpdateView.as_view(), name='entidad_editar'),
    path('entidades/<int:pk>/toggle/', views.entidad_toggle, name='entidad_toggle'),

    # SAQ
    path('saq/', views.saq_view, name='saq'),
]