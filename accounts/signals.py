from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Pupil

@receiver(post_save, sender=User)
def create_pupil_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаем профиль Pupil при создании нового User
    """
    if created:
        Pupil.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_pupil_profile(sender, instance, **kwargs):
    """
    Сохраняем профиль Pupil при создании User
    """
    if hasattr(instance, 'pupil_profile'):
        instance.pupil_profile.save()