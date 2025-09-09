from django.contrib.auth.models import Group, User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def asignar_invitado(sender, instance, created, **kwargs):
    if created:
        invitado_group, _ = Group.objects.get_or_create(name="Invitado")
        instance.groups.add(invitado_group)
