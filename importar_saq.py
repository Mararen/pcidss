import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from users.models import TipoSAQ, SeccionSAQ, PreguntaSAQ, PreguntaEnSeccion

DATA = r'C:\django_proyectos\pcidss\data\aoc_saq.xlsx'

TIPOS_SAQ = {
    'A':   'SAQ A',
    'AEP': 'SAQ A-EP',
    'B':   'SAQ B',
    'BIP': 'SAQ B-IP',
    'C':   'SAQ C',
    'CTV': 'SAQ C-VT',
    'DC':  'SAQ D Comercio',
    'DP':  'SAQ D Proveedor',
}

SECCIONES = {
    '1':  'Requisito 1 – Controles de Seguridad de Red',
    '2':  'Requisito 2 – Configuraciones Seguras del Sistema',
    '3':  'Requisito 3 – Protección de Datos de Cuenta Almacenados',
    '4':  'Requisito 4 – Criptografía en Transmisión',
    '5':  'Requisito 5 – Protección contra Malware',
    '6':  'Requisito 6 – Desarrollo y Mantenimiento de Sistemas Seguros',
    '7':  'Requisito 7 – Restricción de Acceso a Componentes del Sistema',
    '8':  'Requisito 8 – Identificación y Autenticación de Usuarios',
    '9':  'Requisito 9 – Restricción de Acceso Físico',
    '10': 'Requisito 10 – Registro y Monitoreo de Accesos',
    '11': 'Requisito 11 – Pruebas de Seguridad de Sistemas y Redes',
    '12': 'Requisito 12 – Políticas y Programas de Seguridad',
}

# ── Lee el archivo de Excel ────────────────────────────────────────────────────────────────
df = pd.read_excel(DATA)
df.columns = ['referencia', 'texto_pci', 'texto_es', 'texto_en', 'expected_testing',
              'si_si', 'si_no', 'A', 'AEP', 'B', 'BIP', 'C', 'CTV', 'DC', 'DP']

# Gestiona que sean solo filas con referencia y texto válidos
df = df[df['referencia'].notna() & df['texto_es'].notna()].copy()
df['referencia'] = df['referencia'].astype(str).str.strip()
print(f"Preguntas válidas encontradas: {len(df)}")

# ── Limpia los datos anteriores ──────────────────────────────────────────────────
PreguntaEnSeccion.objects.all().delete()
SeccionSAQ.objects.all().delete()
TipoSAQ.objects.all().delete()
PreguntaSAQ.objects.all().delete()
print("Datos SAQ anteriores eliminados.")

# ── Crea TipoSAQ ─────────────────────────────────────────────────────────────
tipos = {}
for clave, nombre in TIPOS_SAQ.items():
    tipo = TipoSAQ.objects.create(nombre=nombre)
    tipos[clave] = tipo
    print(f"  Tipo creado: {nombre}")

# ── Crea SeccionSAQ por tipo ─────────────────────────────────────────────────
secciones = {} 
for tipo_clave, tipo_obj in tipos.items():
    secciones[tipo_clave] = {}
    for num, nombre in SECCIONES.items():
        seccion = SeccionSAQ.objects.create(
            tipo=tipo_obj,
            nombre=nombre,
            orden=int(num),
        )
        secciones[tipo_clave][num] = seccion

print(f"  Secciones creadas: {len(SECCIONES)} por cada tipo SAQ")

# ── Crea PreguntaSAQ y PreguntaEnSeccion ─────────────────────────────────────
tipos_col = ['A', 'AEP', 'B', 'BIP', 'C', 'CTV', 'DC', 'DP']
contadores = {t: 0 for t in tipos_col}

for _, row in df.iterrows():
    referencia = row['referencia']
    num_seccion = referencia.split('.')[0]

    if num_seccion not in SECCIONES:
        continue

    # Crea la pregunta una sola vez
    pregunta = PreguntaSAQ.objects.create(
        texto=str(row['texto_es']).strip(),
        referencia_pci=referencia,
    )

    # Asigna a cada tipo SAQ que le corresponde (flag == 1)
    for col in tipos_col:
        if row[col] == 1:
            seccion_obj = secciones[col].get(num_seccion)
            if seccion_obj:
                orden_actual = PreguntaEnSeccion.objects.filter(seccion=seccion_obj).count() + 1
                PreguntaEnSeccion.objects.create(
                    pregunta=pregunta,
                    seccion=seccion_obj,
                    orden=orden_actual,
                )
                contadores[col] += 1

print("\n✓ Importación SAQ completada:")
for col in tipos_col:
    nombre = TIPOS_SAQ[col]
    print(f"  {nombre}: {contadores[col]} preguntas")