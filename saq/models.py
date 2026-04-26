from django.db import models
from django.contrib.auth.models import User
import json


# ─────────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────────

class TipoSAQ(models.TextChoices):
    A           = 'A',           'SAQ A'
    AEP         = 'AEP',         'SAQ A-EP'
    B           = 'B',           'SAQ B'
    BIP         = 'BIP',         'SAQ B-IP'
    C           = 'C',           'SAQ C'
    CTV         = 'CTV',         'SAQ C-VT'
    D_COMERCIO  = 'D-COMERCIO',  'SAQ D Comercio'
    D_PROVEEDOR = 'D-PROVEEDOR', 'SAQ D Proveedor'


TIPO_INPUT_CHOICES = (
    ('elegibilidad',   'Sí / No / N/A / No probado'),
    ('checkbox_si_no', 'Sí / No'),
    ('checkbox_multi', 'Selección múltiple (casillas)'),
    ('select',         'Lista desplegable'),
    ('texto_corto',    'Texto corto (≤ 200 car.)'),
    ('texto_largo',    'Texto largo (≤ 500 car.)'),
    ('numero',         'Número entero'),
    ('fecha',          'Fecha'),
)


# ─────────────────────────────────────────────
# PREGUNTAS SAQ
# ─────────────────────────────────────────────

class PreguntaSAQ(models.Model):
    """
    Banco de preguntas del PreTest de orientación SAQ.

    tipo_saq         → SAQ primario (para filtros y conteos)
    tipos_saq_extra  → SAQs adicionales separados por coma (ej: 'AEP,B')
                       Vacío si la pregunta solo pertenece a tipo_saq
    tipo_input       → Cómo se captura la respuesta en el formulario
    opciones_json    → Lista de opciones para checkbox_multi / select
    seccion_aoc      → Hoja del AOC de donde proviene la pregunta
    """

    numero            = models.IntegerField(unique=True)
    tipo_saq          = models.CharField(max_length=50, choices=TipoSAQ.choices)
    tipos_saq_extra   = models.CharField(max_length=200, blank=True, default='',
                            help_text='SAQs adicionales separados por coma. Ej: AEP,B')

    tipo_input        = models.CharField(max_length=30, choices=TIPO_INPUT_CHOICES,
                            default='elegibilidad')
    seccion_aoc       = models.CharField(max_length=100, blank=True,
                            default='Part 2h. Eligibility')

    pregunta_es       = models.TextField()
    pregunta_en       = models.TextField(blank=True)

    opciones_json     = models.JSONField(null=True, blank=True,
                            help_text='Lista de opciones para checkbox_multi o select')
    max_chars         = models.IntegerField(null=True, blank=True)

    version_pci       = models.CharField(max_length=10, default='4.0.1')
    activo            = models.BooleanField(default=True)

    class Meta:
        ordering = ['numero']
        verbose_name = 'Pregunta SAQ'
        verbose_name_plural = 'Preguntas SAQ'

    def __str__(self):
        return f'#{self.numero} [{self.tipo_saq}] {self.pregunta_es[:60]}'

    # ── Helpers ──────────────────────────────────────────────────

    def get_todos_los_saq(self):
        """Devuelve lista con todos los SAQs: primario + extras."""
        tipos = [self.tipo_saq]
        if self.tipos_saq_extra:
            tipos += [t.strip() for t in self.tipos_saq_extra.split(',') if t.strip()]
        return tipos

    # Alias para compatibilidad con templates existentes
    def get_tipo_saq_list(self):
        return self.get_todos_los_saq()

    def get_opciones(self):
        if isinstance(self.opciones_json, list):
            return self.opciones_json
        return []

    @property
    def es_elegibilidad(self):
        return self.tipo_input == 'elegibilidad'


# ─────────────────────────────────────────────
# PRETEST
# ─────────────────────────────────────────────

class PreTest(models.Model):

    ESTADO_CHOICES = (
        ('en_progreso', 'En progreso'),
        ('completado',  'Completado'),
    )

    entidad         = models.ForeignKey('users.Entidad', on_delete=models.CASCADE,
                          related_name='pretests')
    estado          = models.CharField(max_length=20, choices=ESTADO_CHOICES,
                          default='en_progreso')
    saq_recomendado = models.CharField(max_length=20, choices=TipoSAQ.choices,
                          null=True, blank=True)
    creado_por      = models.ForeignKey(User, on_delete=models.SET_NULL,
                          null=True, blank=True)
    fecha_creacion  = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'PreTest'
        verbose_name_plural = 'PreTests'

    def __str__(self):
        return f'PreTest #{self.pk} — {self.entidad}'

    def calcular_resultado(self):
        """
        Calcula el resultado por SAQ considerando SÓLO las preguntas
        de tipo 'elegibilidad' (Part 2h del AOC).

        Lógica de elegibilidad:
          - Un SAQ es ELEGIBLE si todas sus preguntas de elegibilidad
            tienen respuesta 'si'.
          - Se recomienda el primero elegible en el orden de simplicidad:
            A → AEP → B → BIP → C → CTV → D-COMERCIO → D-PROVEEDOR
          - Si ninguno es elegible se recomienda el de mayor % de Sí.
        """
        ORDEN = ['A', 'AEP', 'B', 'BIP', 'C', 'CTV', 'D-COMERCIO', 'D-PROVEEDOR']

        # Inicializar conteos
        conteos = {
            t: {'total': 0, 'si': 0, 'no': 0, 'na': 0, 'no_probado': 0,
                'pct': 0, 'elegible': False, 'es_recomendado': False}
            for t in ORDEN
        }

        # Procesar respuestas de elegibilidad
        for resp in self.respuestas.select_related('pregunta').all():
            if not resp.pregunta.es_elegibilidad:
                continue
            val = resp.respuesta_texto or ''
            for saq in resp.pregunta.get_todos_los_saq():
                if saq not in conteos:
                    continue
                conteos[saq]['total'] += 1
                if val in ('si', 'no', 'na', 'no_probado'):
                    conteos[saq][val] += 1

        # Calcular porcentajes y elegibilidad
        for t in ORDEN:
            c = conteos[t]
            c['pct']      = round(c['si'] / c['total'] * 100) if c['total'] else 0
            c['elegible'] = (c['total'] > 0 and c['si'] == c['total'])

        # Determinar recomendado
        # 1) Primero elegible en orden de simplicidad
        recomendado = next((t for t in ORDEN if conteos[t]['elegible']), None)

        # 2) Si ninguno elegible → mayor porcentaje entre los que tienen preguntas
        if not recomendado:
            con_preguntas = [t for t in ORDEN if conteos[t]['total'] > 0]
            if con_preguntas:
                recomendado = max(con_preguntas, key=lambda t: conteos[t]['pct'])

        if recomendado:
            conteos[recomendado]['es_recomendado'] = True

        # Guardar resultado
        self.saq_recomendado = recomendado
        total_resp = self.respuestas.count()
        total_q    = PreguntaSAQ.objects.filter(activo=True).count()
        if total_resp >= total_q > 0:
            self.estado = 'completado'
        self.save(update_fields=['saq_recomendado', 'estado'])

        return conteos

    @staticmethod
    def get_saq_info_todos():
        return {
            'A':           'Comercios e-commerce donde TODOS los elementos de la página de pago provienen de un TPSP certificado PCI DSS (iframe/redirección). No almacenan, procesan ni transmiten datos de tarjeta.',
            'AEP':         'Comercios e-commerce que usan API, JavaScript o Direct Post de un TPSP certificado PCI DSS. La página de pago es propia pero el procesamiento está completamente externalizado.',
            'B':           'Comercios con imprinters manuales o terminales autónomas sin conexión a internet. No almacenan datos de tarjeta en formato electrónico.',
            'BIP':         'Comercios con terminales PTS POI aprobados por PCI conectados por IP al procesador de pagos, completamente aislados de otros sistemas del entorno.',
            'C':           'Comercios con sistema de pago e internet en el mismo dispositivo/LAN, sin conexión a otros sistemas y sin almacenamiento electrónico de datos de tarjeta.',
            'CTV':         'Comercios que procesan pagos únicamente a través de terminal de pago virtual web, provista y alojada por un TPSP certificado PCI DSS.',
            'D-COMERCIO':  'Comercios que almacenan datos de tarjeta electrónicamente o que no califican para ningún SAQ anterior. Requiere cumplir TODOS los requerimientos PCI DSS aplicables.',
            'D-PROVEEDOR': 'Proveedores de servicios que almacenan, procesan o transmiten datos de tarjeta en nombre de terceros. Requiere cumplir TODOS los requerimientos PCI DSS para proveedores.',
        }


# ─────────────────────────────────────────────
# RESPUESTAS
# ─────────────────────────────────────────────

class RespuestaPreTest(models.Model):
    """
    Almacena la respuesta de una pregunta en un PreTest.

    respuesta_texto contiene según tipo_input:
      elegibilidad   → 'si' | 'no' | 'na' | 'no_probado'
      checkbox_si_no → 'si' | 'no'
      checkbox_multi → JSON array  '["opcion1","opcion2"]'
      texto_corto/largo → cadena libre
      fecha          → 'YYYY-MM-DD'
      select         → valor seleccionado
      numero         → cadena numérica
    """

    pretest          = models.ForeignKey(PreTest, on_delete=models.CASCADE,
                           related_name='respuestas')
    pregunta         = models.ForeignKey(PreguntaSAQ, on_delete=models.CASCADE)
    respuesta_texto  = models.TextField(blank=True, default='')
    fecha            = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together     = ('pretest', 'pregunta')
        verbose_name        = 'Respuesta PreTest'
        verbose_name_plural = 'Respuestas PreTest'

    def __str__(self):
        return f'PT#{self.pretest_id} Q#{self.pregunta.numero} → {self.respuesta_texto[:40]}'

    def get_valor_display(self):
        """Valor legible para reportes/resumen."""
        t = self.pregunta.tipo_input
        v = self.respuesta_texto
        if t in ('elegibilidad', 'checkbox_si_no'):
            return {'si': 'Sí', 'no': 'No', 'na': 'N/A',
                    'no_probado': 'No probado'}.get(v, v or '—')
        if t == 'checkbox_multi':
            try:
                return ', '.join(json.loads(v)) or '—'
            except Exception:
                return v or '—'
        return v or '—'