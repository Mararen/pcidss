import pandas as pd
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

from saq.models import Requisito, PreguntaSAQ, SAQ


class Command(BaseCommand):
    help = "Importa preguntas SAQ desde Excel PCI DSS"

    def handle(self, *args, **kwargs):

        excel_path = Path(settings.BASE_DIR) / "data" / "aoc_saq.xlsx"
        df = pd.read_excel(excel_path)

        saq_map = {
            "A": "A",
            "AEP": "AEP",
            "B": "B",
            "BIP": "BIP",
            "C": "C",
            "CTV": "CTV",
            "D-C": "D-C",
            "D-P": "D-P",
        }

        # Crear SAQs
        saqs = {k: SAQ.objects.get_or_create(codigo=k)[0] for k in saq_map}

        creadas = 0

        for _, row in df.iterrows():

            codigo_req = str(row["Testing Procedures"]).strip()
            titulo = str(row["Pregunta PCIDSS"]).strip()
            pregunta = str(row["Pregunta Español"]).strip()

            if not codigo_req or codigo_req.lower().startswith("testing"):
                continue

            requisito, _ = Requisito.objects.get_or_create(
                codigo=codigo_req,
                defaults={"titulo": titulo}
            )

            pregunta_obj, created = PreguntaSAQ.objects.get_or_create(
                requisito=requisito,
                texto=pregunta
            )

            for saq_col, saq_code in saq_map.items():
                if float(row[saq_col]) == 1.0:
                    pregunta_obj.saqs.add(saqs[saq_code])

            if created:
                creadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"Preguntas creadas correctamente: {creadas}")
        )