from django.contrib import admin
from .models import PreguntaSAQ, PreTest, RespuestaPreTest


class RespuestaInline(admin.TabularInline):
    model  = RespuestaPreTest
    extra  = 0
    fields = ('pregunta', 'respuesta_texto', 'fecha')
    readonly_fields = ('fecha',)


@admin.register(PreguntaSAQ)
class PreguntaSAQAdmin(admin.ModelAdmin):
    list_display   = ('numero', 'tipo_saq', 'tipo_input', 'activo', 'version_pci')
    list_filter    = ('tipo_saq', 'tipo_input', 'activo')
    search_fields  = ('pregunta_es', 'pregunta_en')
    ordering       = ('numero',)
    list_per_page  = 30


@admin.register(PreTest)
class PreTestAdmin(admin.ModelAdmin):
    list_display   = ('pk', 'entidad', 'estado', 'saq_recomendado', 'fecha_creacion')
    list_filter    = ('estado', 'saq_recomendado')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    inlines        = [RespuestaInline]


@admin.register(RespuestaPreTest)
class RespuestaPreTestAdmin(admin.ModelAdmin):
    list_display  = ('pretest', 'pregunta_num', 'tipo_input_p', 'respuesta_preview', 'fecha')
    readonly_fields = ('pretest', 'pregunta', 'fecha')

    def pregunta_num(self, obj):
        return f'#{obj.pregunta.numero}'
    pregunta_num.short_description = 'Pregunta'

    def tipo_input_p(self, obj):
        return obj.pregunta.tipo_input
    tipo_input_p.short_description = 'Tipo'

    def respuesta_preview(self, obj):
        return obj.respuesta_texto[:60] or '—'
    respuesta_preview.short_description = 'Respuesta'