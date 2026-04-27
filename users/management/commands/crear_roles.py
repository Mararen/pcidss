from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLES = {
    # ── Roles generales ─────────────────────────────────────────────────────
    "Administrador de Entidad": [
        "ver_dashboard",
        "ver_entidades",
        "gestionar_entidades",
        "gestionar_renovacion",
        "gestionar_configuracion",
    ],
    "Administrador Global": "ALL",
    "Gestor de Contenido": [
        "ver_dashboard",
        "ver_saq",
        "editar_saq",
        "gestionar_configuracion",
    ],
    "Lector de Logs": [
        "ver_dashboard",
        "ver_evidencias",
    ],
    "Revisor de SAQ": [
        "ver_dashboard",
        "ver_saq",
        "usar_pretest",
    ],
    "Usuario de Helpdesk": [
        "ver_dashboard",
        # Helpdesk — todos los permisos
        "add_ticket",
        "change_ticket",
        "delete_ticket",
        "view_ticket",
        "add_categoria",
        "change_categoria",
        "delete_categoria",
        "view_categoria",
        "add_comentarioticket",
        "change_comentarioticket",
        "delete_comentarioticket",
        "view_comentarioticket",
        "add_archivoticket",
        "change_archivoticket",
        "delete_archivoticket",
        "view_archivoticket",
    ],
    "Usuario Estándar": [
        "ver_dashboard",
        "usar_pretest",
        "ver_evidencias",
        "gestionar_renovacion",
        # Helpdesk — solo agregar y ver
        "add_ticket",
        "view_ticket",
        "add_comentarioticket",
        "view_comentarioticket",
    ],

    # ── Usuarios específicos ─────────────────────────────────────────────────

    # userentity001: entidades + pretest (ver y responder) + helpdesk (agregar y ver) + dashboard
    "userentity001": [
        "ver_dashboard",
        # Entidades
        "ver_entidades",
        "gestionar_entidades",
        # PreTest — ver y responder, no crear
        "view_preguntapretest",
        "view_respuestapretest",
        "add_respuestapretest",
        "change_respuestapretest",
        "view_resultadopretest",
        # Helpdesk — solo agregar y ver
        "add_ticket",
        "view_ticket",
        "add_comentarioticket",
        "view_comentarioticket",
    ],

    # usersaq001: SAQ (ver + crear preguntas) + helpdesk (agregar y ver) + dashboard
    # No puede responder PreTests
    "usersaq001": [
        "ver_dashboard",
        # SAQ — ver y crear preguntas
        "ver_saq",
        "add_preguntasaq",
        "view_preguntasaq",
        "change_preguntasaq",
        # Helpdesk — solo agregar y ver
        "add_ticket",
        "view_ticket",
        "add_comentarioticket",
        "view_comentarioticket",
    ],

    # userhelpdesk001: solo dashboard + helpdesk completo
    "userhelpdesk001": [
        "ver_dashboard",
        # Helpdesk — todos los permisos
        "add_ticket",
        "change_ticket",
        "delete_ticket",
        "view_ticket",
        "add_categoria",
        "change_categoria",
        "delete_categoria",
        "view_categoria",
        "add_comentarioticket",
        "change_comentarioticket",
        "delete_comentarioticket",
        "view_comentarioticket",
        "add_archivoticket",
        "change_archivoticket",
        "delete_archivoticket",
        "view_archivoticket",
    ],
}


class Command(BaseCommand):
    help = "Crear roles y asignar permisos"

    def handle(self, *args, **kwargs):
        for nombre, permisos in ROLES.items():
            group, created = Group.objects.get_or_create(name=nombre)
            group.permissions.clear()

            if permisos == "ALL":
                group.permissions.set(Permission.objects.all())
            else:
                for codename in permisos:
                    # filter() en vez de get() para evitar error si el codename
                    # existe en más de una app (ej: add_respuestapretest en saq y pretest)
                    encontrados = Permission.objects.filter(codename=codename)
                    if encontrados.exists():
                        for permiso in encontrados:
                            group.permissions.add(permiso)
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠ Permiso no encontrado: {codename}")
                        )

            accion = "creado" if created else "actualizado"
            self.stdout.write(
                self.style.SUCCESS(f"✔ Rol {accion}: {nombre}")
            )