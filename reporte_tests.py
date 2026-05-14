import pytest
from datetime import datetime

def pytest_html_report_title(report):
    report.title = "Reporte de Pruebas Automatizadas Selenium - PCI Cert Pro"

def pytest_configure(config):
    config._metadata = {
        "Proyecto":     "PCI Cert Pro",
        "Versión":      "1.0.0",
        "Ambiente":     "Desarrollo",
        "Fecha":        datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Responsable":  "Martha Arenas",
        "Estándar":     "PCI DSS v4.0",
        "Apps probadas": "users, saq, catalogos, helpdesk",
    }