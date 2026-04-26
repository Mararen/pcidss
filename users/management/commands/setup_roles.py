from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

ROLES = {
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
    "Helpdesk": [
        "ver_dashboard",
    ],
    "Usuario Estándar": [
        "ver_dashboard",
        "usar_pretest",
        "ver_evidencias",
        "gestionar_renovacion",
    ],
}


class Command(BaseCommand):
    help = "Crear roles y asignar permisos"

    def handle(self, *args, **kwargs):

        for nombre, permisos in ROLES.items():

            group, _ = Group.objects.get_or_create(name=nombre)

            group.permissions.clear()

            if permisos == "ALL":
                group.permissions.set(Permission.objects.all())
            else:
                for codename in permisos:
                    try:
                        permiso = Permission.objects.get(codename=codename)
                        group.permissions.add(permiso)
                    except Permission.DoesNotExist:
                        self.stdout.write(f"Permiso no encontrado: {codename}")

            self.stdout.write(f"Rol creado/actualizado: {nombre}")