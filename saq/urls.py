from django.urls import path
from . import views

app_name = 'saq'

urlpatterns = [
    # ── Banco de Preguntas SAQ ──────────────────────────────────
    path('',                          views.saq_lista,    name='saq_lista'),
    path('crear/',                    views.saq_crear,    name='saq_crear'),
    path('editar/<int:pk>/',          views.saq_editar,   name='saq_editar'),
    path('eliminar/<int:pk>/',        views.saq_eliminar, name='saq_eliminar'),

    # ── PreTest ─────────────────────────────────────────────────
    path('pretest/',                      views.pretest_lista,             name='pretest_lista'),
    path('pretest/nuevo/',                views.pretest_nuevo,             name='pretest_nuevo'),
    path('pretest/<int:pk>/',             views.pretest_cuestionario,      name='pretest_cuestionario'),
    path('pretest/<int:pk>/guardar/',     views.pretest_guardar_respuesta, name='pretest_guardar_respuesta'),
    path('pretest/<int:pk>/resultados/',  views.pretest_resultados,        name='pretest_resultados'),
    path('pretest/<int:pk>/eliminar/',    views.pretest_eliminar,          name='pretest_eliminar'),
]