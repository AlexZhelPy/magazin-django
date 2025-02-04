from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ImageForAvatar

@receiver(pre_save, sender=ImageForAvatar)
def delete_old_file(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = ImageForAvatar.objects.get(pk=instance.pk)
            if old_instance.path and old_instance.path != instance.path:
                old_instance.path.delete(save=False)
        except ImageForAvatar.DoesNotExist:
            pass