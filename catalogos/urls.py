from django.urls import path
from . import views

app_name = "catalogos"

urlpatterns = [
    path('', views.tipo_entidad, name='home'),  # dashboard de catálogos

    # Tipos de entidad
    path("tipo-entidad/", views.tipo_entidad, name="tipo_entidad"),
    path("tipo-entidad/<int:pk>/toggle/", views.tipo_entidad_toggle, name="tipo_entidad_toggle"),
    path("tipo-entidad/<int:pk>/eliminar/", views.tipo_entidad_eliminar, name="tipo_entidad_eliminar"),

    # Países
    path("paises/", views.paises, name="paises"),
    path("paises/<int:pk>/toggle/", views.paises_toggle, name="paises_toggle"),
    path("paises/<int:pk>/eliminar/", views.paises_eliminar, name="paises_eliminar"),

    # Contratos
    path("tipo-contrato/", views.tipo_contrato, name="tipo_contrato"),
    path("tipo-contrato/<int:pk>/toggle/", views.tipo_contrato_toggle, name="tipo_contrato_toggle"),
    path("tipo-contrato/<int:pk>/eliminar/", views.tipo_contrato_eliminar, name="tipo_contrato_eliminar"),

    # Riesgo
    path("nivel-riesgo/", views.nivel_riesgo, name="nivel_riesgo"),
    path("nivel-riesgo/<int:pk>/toggle/", views.nivel_riesgo_toggle, name="nivel_riesgo_toggle"),
    path("nivel-riesgo/<int:pk>/eliminar/", views.nivel_riesgo_eliminar, name="nivel_riesgo_eliminar"),

    # SAQ
    path("tipo-saq/", views.tipo_saq, name="tipo_saq"),
    path("tipo-saq/<int:pk>/toggle/", views.tipo_saq_toggle, name="tipo_saq_toggle"),
    path("tipo-saq/<int:pk>/eliminar/", views.tipo_saq_eliminar, name="tipo_saq_eliminar"),

    # Documento
    path("tipo-documento/", views.tipo_documento, name="tipo_documento"),
    path("tipo-documento/<int:pk>/toggle/", views.tipo_documento_toggle, name="tipo_documento_toggle"),
    path("tipo-documento/<int:pk>/eliminar/", views.tipo_documento_eliminar, name="tipo_documento_eliminar"),

    # Certificación
    path("estado-certificacion/", views.estado_certificacion, name="estado_certificacion"),
    path("estado-certificacion/<int:pk>/toggle/", views.estado_certificacion_toggle, name="estado_certificacion_toggle"),
    path("estado-certificacion/<int:pk>/eliminar/", views.estado_certificacion_eliminar, name="estado_certificacion_eliminar"),

    # Rol
    path("tipo-rol/", views.tipo_rol, name="tipo_rol"),
    path("tipo-rol/<int:pk>/toggle/", views.tipo_rol_toggle, name="tipo_rol_toggle"),
    path("tipo-rol/<int:pk>/eliminar/", views.tipo_rol_eliminar, name="tipo_rol_eliminar"),

    # Idiomas
    path("idiomas/", views.idiomas, name="idiomas"),
    path("idiomas/<int:pk>/toggle/", views.idiomas_toggle, name="idiomas_toggle"),
    path("idiomas/<int:pk>/eliminar/", views.idiomas_eliminar, name="idiomas_eliminar"),
]