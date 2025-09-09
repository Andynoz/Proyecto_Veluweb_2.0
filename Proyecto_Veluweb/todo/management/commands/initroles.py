from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from todo.models import Cliente, Producto, Factura


class Command(BaseCommand):
    help = "Crea grupos Invitado, Empleado y Admin y asigna permisos"

    def handle(self, *args, **options):
        invitado_group, _ = Group.objects.get_or_create(name="Invitado")
        empleado_group, _ = Group.objects.get_or_create(name="Empleado")
        admin_group, _ = Group.objects.get_or_create(name="Admin")

        modelos = [Cliente, Producto, Factura]

        # Empleado: puede agregar y ver
        for model in modelos:
            ct = ContentType.objects.get_for_model(model)
            add_perm = Permission.objects.get(codename=f"add_{model._meta.model_name}", content_type=ct)
            view_perm = Permission.objects.get(codename=f"view_{model._meta.model_name}", content_type=ct)
            empleado_group.permissions.add(add_perm, view_perm)

        # Admin: todos los permisos
        admin_group.permissions.set(Permission.objects.all())

        self.stdout.write(self.style.SUCCESS("Grupos y permisos inicializados"))
