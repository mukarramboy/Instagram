from .models import UserConfirmation, AuthType
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_verification_email

@receiver(post_save, sender=UserConfirmation)
def send_code_on_created(sender, instance, created, **kwargs):
    if created and instance.auth_type == AuthType.Email:
        send_verification_email.delay(instance.user.email, instance.code)




