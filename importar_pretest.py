import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from users.models import PreguntaPreTest

DATA = r'C:\django_proyectos\pcidss\data\pretest.xlsx'

df = pd.read_excel(DATA)
df.columns = ['num', 'saq', 'pregunta_es', 'pregunta_en', 'version']
df = df.iloc[1:].reset_index(drop=True)

PreguntaPreTest.objects.all().delete()
print("Preguntas PreTest anteriores eliminadas.")

creadas = 0
for _, row in df.iterrows():
    PreguntaPreTest.objects.create(
        numero=int(row['num']),
        saq_destino=str(row['saq']).strip(),
        texto_es=str(row['pregunta_es']).strip(),
        texto_en=str(row['pregunta_en']).strip(),
        version_pci=str(row['version']).strip(),
    )
    creadas += 1

print(f"✓ {creadas} preguntas de PreTest importadas correctamente.")